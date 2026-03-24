import unittest

from fastapi import FastAPI

from app.routers import ai_router
from tests.asgi_test_client import ASGITestClient


class QueryPreprocessAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = FastAPI()
        app.include_router(ai_router)
        cls.client = ASGITestClient(app)

    def test_query_preprocess_success_response(self) -> None:
        response = self.client.post(
            "/ai/cafe/query-preprocess",
            {
                "query": "  햇살 좋은 두준국과 커피 맛집  ",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "data": {
                    "original_query": "햇살 좋은 두준국과 커피 맛집",
                    "vector": [],
                    "dimensions": 0,
                    "extracted_menus": [],
                    "menu_count": 0,
                },
            },
        )

    def test_query_preprocess_rejects_blank_query(self) -> None:
        response = self.client.post(
            "/ai/cafe/query-preprocess",
            {
                "query": "   ",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            },
        )

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail[0]["loc"], ["body", "query"])

    def test_query_preprocess_rejects_invalid_uuid(self) -> None:
        response = self.client.post(
            "/ai/cafe/query-preprocess",
            {
                "query": "커피",
                "user_id": "not-a-uuid",
            },
        )

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertEqual(detail[0]["loc"], ["body", "user_id"])
