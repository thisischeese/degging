import asyncio
import copy
import unittest
from contextlib import asynccontextmanager
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from PIL import Image

from app.models.cafe_crawling import CafeCrawlingRequestItem
from app.services import cafe_crawling_runtime, cafe_crawling_service
from app.services.cafe_crawling_service import CafeCrawlingItemError, CafeCrawlingSourceError, CafeSeed, RuntimeSettings


CAFE_ID_1 = "c5383afd-48e0-48f1-863b-33ccd638b410"
CAFE_ID_2 = "bd297883-2f0e-4f5d-bea0-813af23aacd9"
MISSING_CAFE_ID = "11111111-1111-1111-1111-111111111111"
SOURCE_FAIL_CAFE_ID = "22222222-1111-1111-1111-111111111111"


def build_runtime_settings() -> RuntimeSettings:
    return RuntimeSettings(
        s3_secret_key="secret",
        s3_access_key="access",
        s3_bucket_name="bucket",
        s3_region="ap-northeast-2",
        gms_api_key="gms-key",
    )


def build_seed(cafe_id: str, name: str = "test cafe") -> CafeSeed:
    return CafeSeed(
        cafe_id=cafe_id,
        bizes_id="",
        name=name,
        status="OPEN",
        address=None,
        road_address=None,
        lon=None,
        lat=None,
        thumbnail_url=None,
        kakao_place_id=None,
        kakao_map_url=None,
    )


def build_image_bytes(
    width: int,
    height: int,
    *,
    mode: str = "RGB",
    color: tuple[int, ...] = (25, 50, 75),
    format: str = "JPEG",
) -> bytes:
    buffer = BytesIO()
    image = Image.new(mode, (width, height), color)
    image.save(buffer, format=format)
    image.close()
    return buffer.getvalue()


def build_raw_item(seed: CafeSeed, *, menu_count: int = 1, image_count: int = 1, vibe_count: int = 1) -> dict:
    return {
        "cafe_id": seed.cafe_id,
        "cafes": {
            "cafe_id": seed.cafe_id,
            "name": seed.name,
            "thumbnail_url": None,
            "cafe_intro": f"{seed.name} intro",
        },
        "cafe_rating_stats": {
            "review_count": 1,
            "rating_sum": 3,
            "solo_ratio": "50%",
            "date_ratio": "25%",
            "friends_ratio": "25%",
        },
        "cafe_images": [
            {
                "image_url": f"cafes/{seed.cafe_id}/images/{index:02d}.jpg",
                "sort_order": index,
            }
            for index in range(image_count)
        ],
        "cafe_menus": [
            {
                "menu_name": f"menu-{index}",
                "price": 5000 + index,
                "menu_description": None,
            }
            for index in range(menu_count)
        ],
        "cafe_business_hours": {
            "mon_hours": None,
            "tues_hours": None,
            "wed_hours": None,
            "thur_hours": None,
            "fri_hours": None,
            "sat_hours": None,
            "sun_hours": None,
        },
        "cafe_vibe_tags": [
            {
                "tag_id": f"tag-{index}",
            }
            for index in range(vibe_count)
        ],
        "cafe_reviews": [
            {
                "user_id": f"{seed.cafe_id}-user-0",
                "user_review": "nice",
                "rating": 3,
            }
        ],
    }


@asynccontextmanager
async def fake_resources_context_factory(launched_browsers: list[SimpleNamespace], *args, **kwargs):
    async def fake_launch(*launch_args, **launch_kwargs):
        browser = SimpleNamespace(close=AsyncMock())
        launched_browsers.append(browser)
        return browser

    yield SimpleNamespace(
        playwright=SimpleNamespace(chromium=SimpleNamespace(launch=AsyncMock(side_effect=fake_launch))),
        http_client=AsyncMock(),
        gms_client=AsyncMock(),
        s3_client=AsyncMock(),
        tab_concurrency=2,
        image_concurrency=3,
    )


class CafeCrawlingImageProcessingTest(unittest.TestCase):
    def test_prepare_image_for_upload_resizes_landscape_image_with_progressive_jpeg(self) -> None:
        data = build_image_bytes(1600, 1200)

        processed_data, content_type, ext = cafe_crawling_service.prepare_image_for_upload(
            data,
            max_edge_px=cafe_crawling_service.DEFAULT_IMAGE_MAX_EDGE_PX,
        )

        with Image.open(BytesIO(processed_data)) as image:
            self.assertEqual(image.size, (800, 600))
            self.assertTrue(image.info.get("progressive") or image.info.get("progression"))
        self.assertEqual(content_type, "image/jpeg")
        self.assertEqual(ext, ".jpg")

    def test_prepare_image_for_upload_preserves_portrait_ratio_without_upscale(self) -> None:
        portrait_data = build_image_bytes(600, 1200)
        small_data = build_image_bytes(120, 80)

        portrait_output, portrait_type, portrait_ext = cafe_crawling_service.prepare_image_for_upload(
            portrait_data,
            max_edge_px=cafe_crawling_service.DEFAULT_IMAGE_MAX_EDGE_PX,
        )
        small_output, small_type, small_ext = cafe_crawling_service.prepare_image_for_upload(
            small_data,
            max_edge_px=cafe_crawling_service.DEFAULT_IMAGE_MAX_EDGE_PX,
        )

        with Image.open(BytesIO(portrait_output)) as portrait_image:
            self.assertEqual(portrait_image.size, (400, 800))
        with Image.open(BytesIO(small_output)) as small_image:
            self.assertEqual(small_image.size, (120, 80))
        self.assertEqual((portrait_type, portrait_ext), ("image/jpeg", ".jpg"))
        self.assertEqual((small_type, small_ext), ("image/jpeg", ".jpg"))

    def test_prepare_image_for_upload_keeps_transparency_as_png(self) -> None:
        data = build_image_bytes(400, 200, mode="RGBA", color=(200, 50, 25, 128), format="PNG")

        processed_data, content_type, ext = cafe_crawling_service.prepare_image_for_upload(
            data,
            max_edge_px=cafe_crawling_service.THUMBNAIL_MAX_EDGE_PX,
        )

        with Image.open(BytesIO(processed_data)) as image:
            self.assertEqual(image.size, (200, 100))
            self.assertIn("A", image.getbands())
            self.assertIn(image.mode, {"P", "RGBA"})
        self.assertEqual(content_type, "image/png")
        self.assertEqual(ext, ".png")

    def test_prepare_image_for_upload_falls_back_to_640_when_file_is_too_large(self) -> None:
        data = build_image_bytes(1600, 1200)

        with patch.object(cafe_crawling_service, "MAX_UPLOAD_IMAGE_BYTES", 1):
            processed_data, content_type, ext = cafe_crawling_service.prepare_image_for_upload(
                data,
                max_edge_px=cafe_crawling_service.DEFAULT_IMAGE_MAX_EDGE_PX,
            )

        with Image.open(BytesIO(processed_data)) as image:
            self.assertEqual(image.size, (640, 480))
        self.assertEqual(content_type, "image/jpeg")
        self.assertEqual(ext, ".jpg")


class CafeCrawlingRuntimeTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        cafe_crawling_runtime.reset_resource_counters_for_test()

    def test_is_allowed_image_url_only_accepts_real_image_hosts(self) -> None:
        self.assertTrue(
            cafe_crawling_runtime.is_allowed_image_url(
                "https://pup-review-phinf.pstatic.net/sample/upload_image.jpeg"
            )
        )
        self.assertTrue(
            cafe_crawling_runtime.is_allowed_image_url(
                "https://ldb-phinf.pstatic.net/20250325_1/1742860000000abc.jpg?type=f132_132"
            )
        )
        self.assertFalse(
            cafe_crawling_runtime.is_allowed_image_url(
                "https://search.pstatic.net/common/?src=https%3A%2F%2Fexample.com%2Fproxy.jpg"
            )
        )
        self.assertFalse(
            cafe_crawling_runtime.is_allowed_image_url(
                "https://pstatic.net/common/proxy.jpg"
            )
        )

    async def test_crawl_cafes_batch_preserves_order_when_tasks_finish_out_of_order(self) -> None:
        request_items = [
            CafeCrawlingRequestItem(cafeId=CAFE_ID_1, name="alpha"),
            CafeCrawlingRequestItem(cafeId=MISSING_CAFE_ID, name="missing"),
            CafeCrawlingRequestItem(cafeId=CAFE_ID_2, name="beta"),
        ]
        launched_browsers: list[SimpleNamespace] = []

        async def fake_crawl_single_cafe(seed, resources, worker_state):
            if seed.cafe_id == CAFE_ID_2:
                await asyncio.sleep(0.01)
                return build_raw_item(seed, menu_count=1, image_count=1)
            if seed.cafe_id == MISSING_CAFE_ID:
                await asyncio.sleep(0.02)
                raise CafeCrawlingItemError("missing")
            await asyncio.sleep(0.03)
            return build_raw_item(seed, menu_count=2, image_count=2)

        with (
            patch.object(cafe_crawling_runtime, "resolve_runtime_settings", return_value=build_runtime_settings()),
            patch.object(cafe_crawling_runtime, "open_crawl_request_resources", lambda *args, **kwargs: fake_resources_context_factory(launched_browsers)),
            patch.object(cafe_crawling_runtime, "crawl_single_cafe", side_effect=fake_crawl_single_cafe),
        ):
            response = await cafe_crawling_runtime.crawl_cafes_batch(request_items)

        self.assertEqual([item.cafe_id for item in response.items], [CAFE_ID_1, CAFE_ID_2])
        self.assertEqual(response.missing_cafe_ids, [MISSING_CAFE_ID])

    async def test_crawl_cafes_batch_cancels_other_tasks_on_source_error(self) -> None:
        request_items = [
            CafeCrawlingRequestItem(cafeId=CAFE_ID_1, name="slow"),
            CafeCrawlingRequestItem(cafeId=SOURCE_FAIL_CAFE_ID, name="source-fail"),
        ]
        cancelled = asyncio.Event()
        launched_browsers: list[SimpleNamespace] = []

        async def fake_crawl_single_cafe(seed, resources, worker_state):
            if seed.cafe_id == SOURCE_FAIL_CAFE_ID:
                await asyncio.sleep(0.01)
                raise CafeCrawlingSourceError("source unavailable")
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                cancelled.set()
                raise
            return build_raw_item(seed)

        with (
            patch.object(cafe_crawling_runtime, "resolve_runtime_settings", return_value=build_runtime_settings()),
            patch.object(cafe_crawling_runtime, "open_crawl_request_resources", lambda *args, **kwargs: fake_resources_context_factory(launched_browsers)),
            patch.object(cafe_crawling_runtime, "crawl_single_cafe", side_effect=fake_crawl_single_cafe),
        ):
            with self.assertLogs("uvicorn.error", level="WARNING") as logs:
                with self.assertRaises(CafeCrawlingSourceError):
                    await cafe_crawling_runtime.crawl_cafes_batch(request_items)

        self.assertTrue(cancelled.is_set())
        self.assertTrue(all(browser.close.await_count >= 1 for browser in launched_browsers))
        joined_logs = "\n".join(logs.output)
        self.assertIn("Cafe crawling item cancelled", joined_logs)
        self.assertIn(CAFE_ID_1, joined_logs)

    async def test_crawl_cafes_batch_recycles_worker_browser_after_empty_result(self) -> None:
        request_items = [
            CafeCrawlingRequestItem(cafeId=CAFE_ID_1, name="alpha"),
            CafeCrawlingRequestItem(cafeId=CAFE_ID_2, name="beta"),
        ]
        launched_browsers: list[SimpleNamespace] = []

        async def fake_crawl_single_cafe(seed, resources, worker_state):
            if seed.cafe_id == CAFE_ID_1:
                return None
            return build_raw_item(seed, image_count=2)

        with (
            patch.object(cafe_crawling_runtime, "resolve_runtime_settings", return_value=build_runtime_settings()),
            patch.object(cafe_crawling_runtime, "open_crawl_request_resources", lambda *args, **kwargs: fake_resources_context_factory(launched_browsers)),
            patch.object(cafe_crawling_runtime, "crawl_single_cafe", side_effect=fake_crawl_single_cafe),
            patch.object(cafe_crawling_runtime.settings, "cafe_batch_concurrency", 1),
        ):
            with self.assertLogs("uvicorn.error", level="INFO") as logs:
                response = await cafe_crawling_runtime.crawl_cafes_batch(request_items)

        self.assertEqual([item.cafe_id for item in response.items], [CAFE_ID_2])
        self.assertEqual(response.missing_cafe_ids, [])
        self.assertGreaterEqual(len(launched_browsers), 2)
        joined_logs = "\n".join(logs.output)
        self.assertIn("Cafe crawling item produced empty result", joined_logs)
        self.assertIn("event=browser_recycle", joined_logs)
        self.assertIn("requested=2 succeeded=1 missing=0 failed=1", joined_logs)

    async def test_crawl_cafes_batch_recycles_worker_browser_after_threshold(self) -> None:
        request_items = [
            CafeCrawlingRequestItem(cafeId=f"cafe-{index:02d}", name=f"cafe-{index:02d}")
            for index in range(cafe_crawling_runtime.BROWSER_RECYCLE_CAFE_THRESHOLD + 1)
        ]
        launched_browsers: list[SimpleNamespace] = []

        async def fake_crawl_single_cafe(seed, resources, worker_state):
            return build_raw_item(seed, image_count=1)

        with (
            patch.object(cafe_crawling_runtime, "resolve_runtime_settings", return_value=build_runtime_settings()),
            patch.object(cafe_crawling_runtime, "open_crawl_request_resources", lambda *args, **kwargs: fake_resources_context_factory(launched_browsers)),
            patch.object(cafe_crawling_runtime, "crawl_single_cafe", side_effect=fake_crawl_single_cafe),
            patch.object(cafe_crawling_runtime.settings, "cafe_batch_concurrency", 1),
        ):
            with self.assertLogs("uvicorn.error", level="INFO") as logs:
                response = await cafe_crawling_runtime.crawl_cafes_batch(request_items)

        self.assertEqual(response.total, len(request_items))
        self.assertGreaterEqual(len(launched_browsers), 2)
        joined_logs = "\n".join(logs.output)
        self.assertIn("Cafe crawling batch worker setup", joined_logs)
        self.assertIn("event=browser_recycle", joined_logs)

    async def test_crawl_cafes_batch_counts_unexpected_item_failures_without_dropping_them(self) -> None:
        request_items = [
            CafeCrawlingRequestItem(cafeId=CAFE_ID_1, name="alpha"),
            CafeCrawlingRequestItem(cafeId=CAFE_ID_2, name="beta"),
        ]
        launched_browsers: list[SimpleNamespace] = []

        async def fake_crawl_single_cafe(seed, resources, worker_state):
            if seed.cafe_id == CAFE_ID_2:
                raise ValueError("boom")
            return build_raw_item(seed)

        with (
            patch.object(cafe_crawling_runtime, "resolve_runtime_settings", return_value=build_runtime_settings()),
            patch.object(cafe_crawling_runtime, "open_crawl_request_resources", lambda *args, **kwargs: fake_resources_context_factory(launched_browsers)),
            patch.object(cafe_crawling_runtime, "crawl_single_cafe", side_effect=fake_crawl_single_cafe),
        ):
            with self.assertLogs("uvicorn.error", level="INFO") as logs:
                response = await cafe_crawling_runtime.crawl_cafes_batch(request_items)

        self.assertEqual([item.cafe_id for item in response.items], [CAFE_ID_1])
        self.assertEqual(response.missing_cafe_ids, [])
        joined_logs = "\n".join(logs.output)
        self.assertIn("Cafe crawling item unexpected failure", joined_logs)
        self.assertIn("Cafe crawling failed items: count=1", joined_logs)
        self.assertIn("requested=2 succeeded=1 missing=0 failed=1", joined_logs)

    async def test_crawl_cafes_batch_logs_unresolved_result_slots_before_aggregation(self) -> None:
        request_items = [
            CafeCrawlingRequestItem(cafeId=CAFE_ID_1, name="alpha"),
            CafeCrawlingRequestItem(cafeId=CAFE_ID_2, name="beta"),
        ]
        launched_browsers: list[SimpleNamespace] = []

        async def fake_crawl_batch_item(*, index, seed, ordered_results, **kwargs):
            if seed.cafe_id == CAFE_ID_1:
                ordered_results[index] = cafe_crawling_runtime.OrderedCrawlResult(item=build_raw_item(seed))

        with (
            patch.object(cafe_crawling_runtime, "resolve_runtime_settings", return_value=build_runtime_settings()),
            patch.object(cafe_crawling_runtime, "open_crawl_request_resources", lambda *args, **kwargs: fake_resources_context_factory(launched_browsers)),
            patch.object(cafe_crawling_runtime, "_crawl_batch_item", side_effect=fake_crawl_batch_item),
        ):
            with self.assertLogs("uvicorn.error", level="INFO") as logs:
                response = await cafe_crawling_runtime.crawl_cafes_batch(request_items)

        self.assertEqual([item.cafe_id for item in response.items], [CAFE_ID_1])
        self.assertEqual(response.missing_cafe_ids, [])
        joined_logs = "\n".join(logs.output)
        self.assertIn("Cafe crawling unresolved results before aggregation: count=1", joined_logs)
        self.assertIn(CAFE_ID_2, joined_logs)
        self.assertIn("Cafe crawling failed items: count=1", joined_logs)
        self.assertIn("requested=2 succeeded=1 missing=0 failed=1", joined_logs)

    async def test_upload_cafe_images_preserves_thumbnail_and_sort_order(self) -> None:
        seed = build_seed(CAFE_ID_1)
        source_data = build_image_bytes(1600, 1200)

        async def fake_download_image_bytes(url, http_client):
            delay_by_index = {"00": 0.03, "01": 0.01, "02": 0.02}
            await asyncio.sleep(delay_by_index[url[-6:-4]])
            return source_data, "image/jpeg"

        fake_s3 = AsyncMock()
        uploaded_images: dict[str, tuple[tuple[int, int], str]] = {}

        async def fake_upload_bytes(key, data, content_type):
            with Image.open(BytesIO(data)) as image:
                uploaded_images[key] = (image.size, content_type)
            return key

        fake_s3.upload_bytes = AsyncMock(side_effect=fake_upload_bytes)

        with patch.object(cafe_crawling_runtime, "download_image_bytes", side_effect=fake_download_image_bytes):
            thumbnail_url, image_rows = await cafe_crawling_runtime.upload_cafe_images(
                seed,
                fake_s3,
                AsyncMock(),
                [
                    "https://example.com/images/00.jpg",
                    "https://example.com/images/01.jpg",
                    "https://example.com/images/02.jpg",
                ],
                max_concurrency=3,
            )

        self.assertTrue(thumbnail_url.endswith("/00.jpg"))
        self.assertEqual([row["image_url"].split("/")[-1] for row in image_rows], ["01.jpg", "02.jpg"])
        self.assertEqual([row["sort_order"] for row in image_rows], [0, 1])
        self.assertEqual(uploaded_images[thumbnail_url], ((200, 150), "image/jpeg"))
        self.assertEqual(uploaded_images[image_rows[0]["image_url"]], ((800, 600), "image/jpeg"))
        self.assertEqual(uploaded_images[image_rows[1]["image_url"]], ((800, 600), "image/jpeg"))

    def test_assign_sequence_ids_preserves_nested_payloads(self) -> None:
        raw_items = [
            build_raw_item(build_seed(CAFE_ID_1), menu_count=2, image_count=2, vibe_count=2),
            build_raw_item(build_seed(CAFE_ID_2), menu_count=1, image_count=1, vibe_count=1),
        ]

        first = cafe_crawling_runtime.assign_sequence_ids(copy.deepcopy(raw_items))
        second = cafe_crawling_runtime.assign_sequence_ids(copy.deepcopy(raw_items))

        self.assertEqual(
            [[image.image_url for image in item.cafe_images] for item in first],
            [[image.image_url for image in item.cafe_images] for item in second],
        )
        self.assertEqual(
            [[menu.menu_name for menu in item.cafe_menus] for item in first],
            [[menu.menu_name for menu in item.cafe_menus] for item in second],
        )
        self.assertEqual(
            [[tag.tag_id for tag in item.cafe_vibe_tags] for item in first],
            [[tag.tag_id for tag in item.cafe_vibe_tags] for item in second],
        )

    async def test_close_failures_keep_resource_counters_non_negative(self) -> None:
        class FailingCloser:
            async def close(self):
                raise RuntimeError("close failed")

        worker_state = cafe_crawling_runtime.WorkerBrowserState(worker_id=1, browser_generation=2)
        seed = build_seed(CAFE_ID_1)

        cafe_crawling_runtime._adjust_resource_counter("active_contexts", 1)
        cafe_crawling_runtime._adjust_resource_counter("active_pages", 1)

        with self.assertLogs("uvicorn.error", level="WARNING") as logs:
            await cafe_crawling_runtime.close_tracked_context(
                FailingCloser(),
                worker_state=worker_state,
                seed=seed,
            )
            await cafe_crawling_runtime.close_tracked_page(
                FailingCloser(),
                worker_state=worker_state,
                seed=seed,
                page_scope="photo",
            )

        snapshot = cafe_crawling_runtime.get_resource_counters_snapshot()
        self.assertEqual(snapshot["active_contexts"], 0)
        self.assertEqual(snapshot["active_pages"], 0)
        self.assertGreaterEqual(snapshot["browser_launches"], 0)
        self.assertGreaterEqual(snapshot["browser_recycles"], 0)
        self.assertTrue(worker_state.needs_recycle)
        joined_logs = "\n".join(logs.output)
        self.assertIn("Cafe crawling context close failed", joined_logs)
        self.assertIn("Cafe crawling page close failed", joined_logs)
