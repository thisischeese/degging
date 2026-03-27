import unittest
from datetime import datetime, timezone
from uuid import UUID

from fastapi import FastAPI

from app.routers import ai_router
from app.routers.onboarding import get_onboarding_service
from app.services.onboarding_service import OnboardingResult
from tests.asgi_test_client import ASGITestClient


class FakeOnboardingService:
    def __init__(self, result: OnboardingResult) -> None:
        self._result = result
        self.last_request = None

    async def onboard(self, request):
        self.last_request = request
        return self._result


class OnboardingAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(ai_router)
        self.client = ASGITestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_onboarding_returns_success_envelope(self) -> None:
        updated_at = datetime(2026, 3, 27, 8, 15, 0, tzinfo=timezone.utc)
        fake_service = FakeOnboardingService(
            OnboardingResult(
                user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
                updated_at=updated_at,
            )
        )
        self.app.dependency_overrides[get_onboarding_service] = lambda: fake_service

        response = self.client.post(
            "/ai/onboarding",
            {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "nickname": "newuser01",
                "email": "newuser01@example.com",
                "favorite_menus": ["두쫀쿠"],
                "mood_tags": ["우드톤/따뜻한"],
                "cafes": ["123e4567-e89b-12d3-a456-426614174001"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Onboarding completed successfully.",
                "data": {
                    "user_id": "123e4567-e89b-12d3-a456-426614174000",
                    "updated_at": "2026-03-27T08:15:00Z",
                },
            },
        )
        self.assertIsNotNone(fake_service.last_request)

    def test_onboarding_rejects_invalid_email(self) -> None:
        response = self.client.post(
            "/ai/onboarding",
            {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "nickname": "newuser01",
                "email": "invalid-email",
                "favorite_menus": ["두쫀쿠"],
                "mood_tags": ["우드톤/따뜻한"],
                "cafes": ["123e4567-e89b-12d3-a456-426614174001"],
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["body", "email"])

    def test_onboarding_rejects_empty_favorite_menus(self) -> None:
        response = self.client.post(
            "/ai/onboarding",
            {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "nickname": "newuser01",
                "email": "newuser01@example.com",
                "favorite_menus": [],
                "mood_tags": ["우드톤/따뜻한"],
                "cafes": ["123e4567-e89b-12d3-a456-426614174001"],
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["body", "favorite_menus"])

    def test_onboarding_rejects_more_than_three_cafes(self) -> None:
        response = self.client.post(
            "/ai/onboarding",
            {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "nickname": "newuser01",
                "email": "newuser01@example.com",
                "favorite_menus": ["두쫀쿠"],
                "mood_tags": ["우드톤/따뜻한"],
                "cafes": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002",
                    "123e4567-e89b-12d3-a456-426614174003",
                    "123e4567-e89b-12d3-a456-426614174004",
                ],
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"][0]["loc"], ["body", "cafes"])
