import asyncio
import copy
import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.models.cafe_crawling import CafeCrawlingRequestItem
from app.services import cafe_crawling_runtime
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
async def fake_resources_context(*args, **kwargs):
    yield SimpleNamespace(batch_semaphore=asyncio.Semaphore(3))


class CafeCrawlingRuntimeTest(unittest.IsolatedAsyncioTestCase):
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

        async def fake_crawl_single_cafe(seed, resources):
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
            patch.object(cafe_crawling_runtime, "open_crawl_request_resources", fake_resources_context),
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

        async def fake_crawl_single_cafe(seed, resources):
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
            patch.object(cafe_crawling_runtime, "open_crawl_request_resources", fake_resources_context),
            patch.object(cafe_crawling_runtime, "crawl_single_cafe", side_effect=fake_crawl_single_cafe),
        ):
            with self.assertRaises(CafeCrawlingSourceError):
                await cafe_crawling_runtime.crawl_cafes_batch(request_items)

        self.assertTrue(cancelled.is_set())

    async def test_upload_cafe_images_preserves_thumbnail_and_sort_order(self) -> None:
        seed = build_seed(CAFE_ID_1)

        async def fake_download_image_bytes(url, http_client):
            delay_by_index = {"00": 0.03, "01": 0.01, "02": 0.02}
            await asyncio.sleep(delay_by_index[url[-6:-4]])
            return b"image-bytes", "image/jpeg"

        fake_s3 = AsyncMock()
        fake_s3.upload_bytes = AsyncMock(side_effect=lambda key, data, content_type: key)

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
