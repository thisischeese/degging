import asyncio
import unittest
from io import BytesIO
from unittest.mock import AsyncMock, patch

from PIL import Image

from app.services import cafe_crawling_service
from app.services.cafe_crawling_service import (
    CafeCrawlingSourceError,
    CafeSeed,
    MAX_REVIEWS,
    RuntimeSettings,
    SequenceState,
    build_cafe_reviews,
    is_allowed_place_category,
    normalize_place_category,
    parse_business_hours,
    parse_review_metrics,
    parse_structured_visitor_reviews,
    parse_total_review_count,
    resolve_runtime_settings,
    tokenize_place_category,
    upload_cafe_images,
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


class CafeCrawlingServiceRuntimeTest(unittest.TestCase):
    def test_runtime_settings_are_resolved_from_app_settings(self) -> None:
        with (
            patch.object(cafe_crawling_service.settings, "s3_secret_key", "secret"),
            patch.object(cafe_crawling_service.settings, "s3_access_key", "access"),
            patch.object(cafe_crawling_service.settings, "s3_bucket_name", "bucket"),
            patch.object(cafe_crawling_service.settings, "s3_region", "ap-northeast-2"),
            patch.object(cafe_crawling_service.settings, "gms_api_key", "gms-key"),
        ):
            runtime_settings = resolve_runtime_settings()

        self.assertEqual(
            runtime_settings,
            RuntimeSettings(
                s3_secret_key="secret",
                s3_access_key="access",
                s3_bucket_name="bucket",
                s3_region="ap-northeast-2",
                gms_api_key="gms-key",
            ),
        )

    def test_runtime_settings_raise_when_required_env_values_are_missing(self) -> None:
        with (
            patch.object(cafe_crawling_service.settings, "s3_secret_key", None),
            patch.object(cafe_crawling_service.settings, "s3_access_key", "access"),
            patch.object(cafe_crawling_service.settings, "s3_bucket_name", "bucket"),
            patch.object(cafe_crawling_service.settings, "s3_region", "ap-northeast-2"),
            patch.object(cafe_crawling_service.settings, "gms_api_key", "gms-key"),
        ):
            with self.assertRaises(CafeCrawlingSourceError) as exc_info:
                resolve_runtime_settings()

        self.assertIn("S3_SECRET_KEY", str(exc_info.exception))

    def test_windows_selector_loop_is_rejected_before_playwright_starts(self) -> None:
        selector_loop = type("_WindowsSelectorEventLoop", (), {})()

        with (
            patch.object(cafe_crawling_service.sys, "platform", "win32"),
            patch.object(cafe_crawling_service.asyncio, "get_running_loop", return_value=selector_loop),
        ):
            with self.assertRaises(CafeCrawlingSourceError) as exc_info:
                cafe_crawling_service.ensure_playwright_runtime_supported()

        self.assertIn("selector loop", str(exc_info.exception))

    def test_non_selector_loop_is_allowed(self) -> None:
        proactor_loop = type("ProactorEventLoop", (), {})()

        with (
            patch.object(cafe_crawling_service.sys, "platform", "win32"),
            patch.object(cafe_crawling_service.asyncio, "get_running_loop", return_value=proactor_loop),
        ):
            cafe_crawling_service.ensure_playwright_runtime_supported()

    def test_uploaded_images_return_s3_keys_instead_of_presigned_urls(self) -> None:
        seed = CafeSeed(
            cafe_id="46537625-27db-4bd0-b9f4-d87c112183ff",
            bizes_id="BIZ123",
            name="테스트카페",
            status="OPEN",
            address=None,
            road_address=None,
            lon=None,
            lat=None,
            thumbnail_url=None,
            kakao_place_id=None,
            kakao_map_url=None,
        )
        source_data = build_image_bytes(1600, 1200)
        uploaded_images: dict[str, tuple[tuple[int, int], str]] = {}
        s3_client = AsyncMock()

        async def fake_upload_bytes(key, data, content_type):
            with Image.open(BytesIO(data)) as image:
                uploaded_images[key] = (image.size, content_type)
            return key

        s3_client.upload_bytes = AsyncMock(side_effect=fake_upload_bytes)

        with patch.object(
            cafe_crawling_service,
            "download_image_bytes",
            AsyncMock(return_value=(source_data, "image/jpeg")),
        ):
            thumbnail_url, image_rows = asyncio.run(
                upload_cafe_images(
                    seed,
                    s3_client,
                    [
                        "https://example.com/images/00.jpg",
                        "https://example.com/images/01.jpg",
                    ],
                    SequenceState(),
                )
            )

        self.assertEqual(
            thumbnail_url,
            "cafes/46537625-27db-4bd0-b9f4-d87c112183ff/images/00.jpg",
        )
        self.assertEqual(
            image_rows[0]["image_url"],
            "cafes/46537625-27db-4bd0-b9f4-d87c112183ff/images/01.jpg",
        )
        self.assertEqual(uploaded_images[thumbnail_url], ((200, 150), "image/jpeg"))
        self.assertEqual(uploaded_images[image_rows[0]["image_url"]], ((800, 600), "image/jpeg"))


class CafeCrawlingReviewMetricsTest(unittest.TestCase):
    def build_review(
        self,
        index: int,
        *,
        rating: int | None,
        companion_type: str = "친구",
        visit_purpose: str = "일상",
    ) -> dict[str, object]:
        return {
            "reviewer_name": f"reviewer-{index}",
            "rating": rating,
            "review_text": f"테스트 리뷰 {index}",
            "visit_purpose": visit_purpose,
            "companion_type": companion_type,
        }

    def test_parse_total_review_count_caps_reviews_at_max(self) -> None:
        self.assertEqual(parse_total_review_count(12), MAX_REVIEWS)
        self.assertEqual(parse_total_review_count([self.build_review(index, rating=5) for index in range(8)]), 8)

    def test_parse_structured_visitor_reviews_reads_rating_from_accessibility_label(self) -> None:
        reviews = parse_structured_visitor_reviews(
            [
                {
                    "lines": [
                        "리뷰어",
                        "리뷰 12",
                        "일상 친구",
                        "별점 텍스트 없이도 리뷰를 저장합니다.",
                    ],
                    "rating_text": "별점 4.0점",
                }
            ]
        )

        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["rating"], 4)
        self.assertEqual(reviews[0]["review_text"], "별점 텍스트 없이도 리뷰를 저장합니다.")

    def test_parse_review_metrics_uses_collected_review_count_for_rating_sum(self) -> None:
        collected_reviews = [self.build_review(index, rating=5) for index in range(MAX_REVIEWS + 2)]

        metrics = parse_review_metrics("방문자 리뷰 132", visitor_reviews=collected_reviews)

        self.assertEqual(metrics["review_count"], MAX_REVIEWS)
        self.assertEqual(metrics["rating_sum"], MAX_REVIEWS * 3)
        self.assertEqual(len(metrics["reviews"]), MAX_REVIEWS)

    def test_parse_review_metrics_preserves_collected_count_below_max(self) -> None:
        collected_reviews = [self.build_review(index, rating=4) for index in range(8)]

        metrics = parse_review_metrics("방문자 리뷰 132", visitor_reviews=collected_reviews)

        self.assertEqual(metrics["review_count"], 8)
        self.assertEqual(metrics["rating_sum"], 24)
        self.assertEqual(len(metrics["reviews"]), 8)

    def test_parse_review_metrics_falls_back_to_text_parser_when_structured_reviews_are_missing(self) -> None:
        fallback_reviews = [
            self.build_review(0, rating=None, companion_type="친구"),
            self.build_review(1, rating=None, companion_type="친구"),
        ]

        with patch.object(cafe_crawling_service, "parse_visitor_reviews", return_value=fallback_reviews):
            metrics = parse_review_metrics("방문자 리뷰 132", visitor_reviews=[])

        self.assertEqual(metrics["review_count"], 2)
        self.assertEqual(metrics["rating_sum"], 6)
        self.assertEqual(metrics["friends_ratio"], "100%")

    def test_build_cafe_reviews_adds_fixed_rating_field(self) -> None:
        seed = CafeSeed(
            cafe_id="46537625-27db-4bd0-b9f4-d87c112183ff",
            bizes_id="BIZ123",
            name="테스트카페",
            status="OPEN",
            address=None,
            road_address=None,
            lon=None,
            lat=None,
            thumbnail_url=None,
            kakao_place_id=None,
            kakao_map_url=None,
        )

        cafe_reviews = build_cafe_reviews(
            seed,
            [
                {
                    "reviewer_name": "reviewer-1",
                    "review_text": "테스트 리뷰 본문",
                }
            ],
        )

        self.assertEqual(len(cafe_reviews), 1)
        self.assertEqual(cafe_reviews[0]["rating"], 3)


class CafeCrawlingBusinessHoursParsingTest(unittest.TestCase):
    def test_parse_business_hours_supports_daily_schedule(self) -> None:
        parsed = parse_business_hours("\uc601\uc5c5\uc2dc\uac04\n\ub9e4\uc77c 08:00 - 20:00")

        self.assertEqual(
            parsed,
            {
                "mon_hours": "08:00 - 20:00",
                "tues_hours": "08:00 - 20:00",
                "wed_hours": "08:00 - 20:00",
                "thur_hours": "08:00 - 20:00",
                "fri_hours": "08:00 - 20:00",
                "sat_hours": "08:00 - 20:00",
                "sun_hours": "08:00 - 20:00",
            },
        )

    def test_parse_business_hours_supports_weekday_and_weekend_schedule(self) -> None:
        parsed = parse_business_hours("\uc601\uc5c5\uc2dc\uac04\n\ud3c9\uc77c 09:00 - 18:00\n\uc8fc\ub9d0 \ud734\ubb34")

        self.assertEqual(parsed["mon_hours"], "09:00 - 18:00")
        self.assertEqual(parsed["fri_hours"], "09:00 - 18:00")
        self.assertEqual(parsed["sat_hours"], "\ud734\ubb34")
        self.assertEqual(parsed["sun_hours"], "\ud734\ubb34")


class CafeCrawlingPlaceCategoryTest(unittest.TestCase):
    def test_normalize_place_category_compacts_whitespace(self) -> None:
        self.assertEqual(
            normalize_place_category("  \uce74\ud398   /   \ub514\uc800\ud2b8  "),
            "\uce74\ud398 / \ub514\uc800\ud2b8",
        )
        self.assertIsNone(normalize_place_category("   "))

    def test_tokenize_place_category_splits_common_delimiters(self) -> None:
        self.assertEqual(
            tokenize_place_category("\uce74\ud398 / \ub514\uc800\ud2b8 \u00b7 \ubca0\uc774\ucee4\ub9ac"),
            ["\uce74\ud398", "\ub514\uc800\ud2b8", "\ubca0\uc774\ucee4\ub9ac"],
        )

    def test_is_allowed_place_category_accepts_configured_keywords_and_compounds(self) -> None:
        allowed_categories = [
            "\uce74\ud398",
            "\uce74\ud398,\ub514\uc800\ud2b8",
            "\ub514\uc800\ud2b8",
            "\ubca0\uc774\ucee4\ub9ac",
            "\ub514\uc800\ud2b8\uce74\ud398",
            "\ubca0\uc774\ucee4\ub9ac\uce74\ud398",
            "\uc2a4\ud130\ub514\uce74\ud398",
        ]

        for category in allowed_categories:
            with self.subTest(category=category):
                self.assertTrue(is_allowed_place_category(category))

    def test_is_allowed_place_category_rejects_non_cafe_categories(self) -> None:
        rejected_categories = [
            None,
            "",
            "   ",
            "\ud559\uc6d0",
            "\uad50\uc2b5\uc18c",
            "\uc0ac\uc9c4\uad00",
        ]

        for category in rejected_categories:
            with self.subTest(category=category):
                self.assertFalse(is_allowed_place_category(category))
