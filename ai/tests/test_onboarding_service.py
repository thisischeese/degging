from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest.mock import patch
from uuid import UUID

from app.models.onboarding import OnboardingRequest
from app.services.onboarding_service import OnboardingService
from app.services.preference_vector import INSERT_USER_PREFERENCE_QUERY, UPDATE_USER_PREFERENCE_QUERY


class FakeInferenceEngine:
    def __init__(self, vector: list[float]) -> None:
        self._vector = vector
        self.calls: list[dict[str, object]] = []

    def vectorize_user(
        self,
        *,
        nickname: str,
        email: str,
        favorite_menus: list[str],
        mood_tags: list[str],
        cafes: list[UUID],
    ) -> list[float]:
        self.calls.append(
            {
                "nickname": nickname,
                "email": email,
                "favorite_menus": favorite_menus,
                "mood_tags": mood_tags,
                "cafes": cafes,
            }
        )
        return self._vector


class FakeTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, responses: list[dict[str, object] | None]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    async def fetchrow(self, query: str, *args: object):
        self.calls.append((query, args))
        return self._responses.pop(0)

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()


class FakeAcquire:
    def __init__(self, connection: FakeConnection):
        self._connection = connection

    async def __aenter__(self) -> FakeConnection:
        return self._connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, connection: FakeConnection):
        self._connection = connection

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self._connection)


class OnboardingServiceTest(unittest.IsolatedAsyncioTestCase):
    def _request(self) -> OnboardingRequest:
        return OnboardingRequest(
            user_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            nickname="newuser01",
            email="newuser01@example.com",
            favorite_menus=["두쫀쿠"],
            mood_tags=["우드톤/따뜻한"],
            cafes=[UUID("123e4567-e89b-12d3-a456-426614174001")],
        )

    async def test_onboard_inserts_new_preference_vector(self) -> None:
        updated_at = datetime(2026, 3, 27, 9, 0, tzinfo=timezone.utc)
        connection = FakeConnection([None, {"updated_at": updated_at}])
        pool = FakePool(connection)
        inference = FakeInferenceEngine([0.1] * 64)
        service = OnboardingService(inference_engine=inference)

        with patch("app.services.onboarding_service.get_pg_pool", return_value=pool):
            result = await service.onboard(self._request())

        self.assertEqual(result.updated_at, updated_at)
        self.assertEqual(connection.calls[0][0], UPDATE_USER_PREFERENCE_QUERY)
        self.assertEqual(connection.calls[1][0], INSERT_USER_PREFERENCE_QUERY)
        self.assertEqual(inference.calls[0]["favorite_menus"], ["두쫀쿠"])

    async def test_onboard_updates_existing_preference_vector(self) -> None:
        updated_at = datetime(2026, 3, 27, 9, 30, tzinfo=timezone.utc)
        connection = FakeConnection([{"updated_at": updated_at}])
        pool = FakePool(connection)
        inference = FakeInferenceEngine([0.2] * 64)
        service = OnboardingService(inference_engine=inference)

        with patch("app.services.onboarding_service.get_pg_pool", return_value=pool):
            result = await service.onboard(self._request())

        self.assertEqual(result.updated_at, updated_at)
        self.assertEqual(len(connection.calls), 1)
        self.assertEqual(connection.calls[0][0], UPDATE_USER_PREFERENCE_QUERY)
        vector_literal = connection.calls[0][1][1]
        self.assertTrue(vector_literal.startswith("["))
        self.assertEqual(len(vector_literal.strip("[]").split(",")), 64)
