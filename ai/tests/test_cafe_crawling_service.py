import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.services import cafe_crawling_service
from app.services.cafe_crawling_service import (
    CafeCrawlingSourceError,
    CafeSeed,
    RuntimeSettings,
    SequenceState,
    resolve_runtime_settings,
    upload_cafe_images,
)


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
        s3_client = AsyncMock()
        s3_client.upload_bytes = AsyncMock(
            side_effect=[
                "cafes/46537625-27db-4bd0-b9f4-d87c112183ff/images/00.jpg",
                "cafes/46537625-27db-4bd0-b9f4-d87c112183ff/images/01.jpg",
            ]
        )

        with patch.object(
            cafe_crawling_service,
            "download_image_bytes",
            AsyncMock(return_value=(b"image-bytes", "image/jpeg")),
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
