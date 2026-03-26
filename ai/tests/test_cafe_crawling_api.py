import unittest

from fastapi import FastAPI

from app.main import app as main_app
from app.models.cafe_crawling import CafeCrawlingResponse
from app.routers import ai_router
from app.routers.cafes import get_cafe_crawling_service
from app.services.cafe_crawling_service import CafeCrawlingSourceError
from tests.asgi_test_client import ASGITestClient


CAFE_ID_1 = "c5383afd-48e0-48f1-863b-33ccd638b410"
CAFE_ID_2 = "bd297883-2f0e-4f5d-bea0-813af23aacd9"
MISSING_CAFE_ID = "11111111-1111-1111-1111-111111111111"
FILTERED_CAFE_ID = "33333333-1111-1111-1111-111111111111"


def build_item(cafe_id: str, name: str, review_count: int) -> dict:
    reviews = []
    if review_count:
        reviews = [
            {
                "user_id": f"{cafe_id}-user-{index}",
                "user_review": f"{name} review {index}",
                "rating": 3,
            }
            for index in range(review_count)
        ]

    return {
        "cafe_id": cafe_id,
        "cafes": {
            "cafe_id": cafe_id,
            "name": name,
            "thumbnail_url": None,
            "cafe_intro": f"{name} intro",
        },
        "cafe_rating_stats": {
            "review_count": review_count,
            "rating_sum": review_count * 3,
            "solo_ratio": "50%",
            "date_ratio": "25%",
            "friends_ratio": "25%",
        },
        "cafe_images": [],
        "cafe_menus": [
            {
                "menu_name": "Americano",
                "price": 4500,
                "menu_description": None,
                "menu_img_url": None,
            }
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
        "cafe_vibe_tags": [],
        "cafe_reviews": reviews,
    }


class FakeCafeCrawlingService:
    def __init__(self, *, should_raise: bool = False) -> None:
        self._should_raise = should_raise

    async def crawl_cafes(self, request_items):
        if self._should_raise:
            raise CafeCrawlingSourceError("crawler runtime is unavailable")

        items = []
        missing_cafe_ids = []
        for request_item in request_items:
            if request_item.cafeId in {MISSING_CAFE_ID, FILTERED_CAFE_ID}:
                missing_cafe_ids.append(request_item.cafeId)
                continue

            review_count = 2 if request_item.cafeId == CAFE_ID_1 else 0
            items.append(build_item(request_item.cafeId, request_item.name, review_count))

        return CafeCrawlingResponse.model_validate(
            {
                "items": items,
                "total": len(items),
                "missing_cafe_ids": missing_cafe_ids,
            }
        )


class CafeCrawlingAPITest(unittest.TestCase):
    def build_client(self, *, should_raise: bool = False) -> ASGITestClient:
        app = FastAPI()
        app.include_router(ai_router)
        app.dependency_overrides[get_cafe_crawling_service] = lambda: FakeCafeCrawlingService(
            should_raise=should_raise
        )
        return ASGITestClient(app)

    def test_cafe_crawling_preserves_order_with_minimal_request_shape(self) -> None:
        client = self.build_client()

        response = client.post(
            "/ai/cafes/crawling",
            [
                {"cafeId": CAFE_ID_2, "name": "감성카페"},
                {"cafeId": CAFE_ID_1, "name": "테스트카페"},
            ],
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 2)
        self.assertEqual(payload["missing_cafe_ids"], [])
        self.assertEqual([item["cafe_id"] for item in payload["items"]], [CAFE_ID_2, CAFE_ID_1])
        self.assertEqual(payload["items"][0]["cafe_reviews"], [])
        self.assertEqual(len(payload["items"][1]["cafe_reviews"]), 2)
        self.assertEqual(payload["items"][1]["cafe_reviews"][0]["rating"], 3)
        self.assertIn("menu_img_url", payload["items"][0]["cafe_menus"][0])
        self.assertIsNone(payload["items"][0]["cafe_menus"][0]["menu_img_url"])
        self.assertIn("cafes", payload["items"][0])
        self.assertIn("cafe_rating_stats", payload["items"][0])
        self.assertIn("cafe_business_hours", payload["items"][0])

    def test_cafe_crawling_returns_partial_success_for_missing_ids(self) -> None:
        client = self.build_client()

        response = client.post(
            "/ai/cafes/crawling",
            [
                {"cafeId": CAFE_ID_1, "name": "테스트카페"},
                {"cafeId": MISSING_CAFE_ID, "name": "유실카페"},
                {"cafeId": CAFE_ID_2, "name": "감성카페"},
            ],
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 2)
        self.assertEqual(payload["missing_cafe_ids"], [MISSING_CAFE_ID])
        self.assertEqual([item["cafe_id"] for item in payload["items"]], [CAFE_ID_1, CAFE_ID_2])

    def test_cafe_crawling_reports_category_filtered_ids_as_missing(self) -> None:
        client = self.build_client()

        response = client.post(
            "/ai/cafes/crawling",
            [
                {"cafeId": FILTERED_CAFE_ID, "name": "\ud559\uc6d0 \uc608\uc2dc"},
                {"cafeId": CAFE_ID_1, "name": "\ud14c\uc2a4\ud2b8\uce74\ud398"},
            ],
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["missing_cafe_ids"], [FILTERED_CAFE_ID])
        self.assertEqual([item["cafe_id"] for item in payload["items"]], [CAFE_ID_1])

    def test_cafe_crawling_rejects_non_array_body(self) -> None:
        client = self.build_client()

        response = client.post("/ai/cafes/crawling", {"cafeId": CAFE_ID_1, "name": "테스트카페"})

        self.assertEqual(response.status_code, 422)

    def test_cafe_crawling_rejects_missing_cafe_id(self) -> None:
        client = self.build_client()

        response = client.post(
            "/ai/cafes/crawling",
            [{"name": "카페 이름만 있음"}],
        )

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail[0]["loc"], ["body", 0, "cafeId"])

    def test_cafe_crawling_rejects_missing_name(self) -> None:
        client = self.build_client()

        response = client.post("/ai/cafes/crawling", [{"cafeId": CAFE_ID_1}])

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail[0]["loc"], ["body", 0, "name"])

    def test_cafe_crawling_rejects_legacy_extra_fields(self) -> None:
        client = self.build_client()

        response = client.post(
            "/ai/cafes/crawling",
            [{"cafeId": CAFE_ID_1, "name": "테스트카페", "bizesId": "BIZ123"}],
        )

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail[0]["loc"], ["body", 0, "bizesId"])

    def test_cafe_crawling_returns_500_when_crawler_runtime_fails(self) -> None:
        client = self.build_client(should_raise=True)

        response = client.post("/ai/cafes/crawling", [{"cafeId": CAFE_ID_1, "name": "테스트카페"}])

        self.assertEqual(response.status_code, 500)
        self.assertIn("crawler runtime", response.json()["detail"])

    def test_metrics_endpoint_exposes_prometheus_payload(self) -> None:
        client = ASGITestClient(main_app)

        response = client.get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", dict(response.headers)["content-type"])
        self.assertIn("cafe_crawling_stage_seconds", response.body.decode("utf-8"))
