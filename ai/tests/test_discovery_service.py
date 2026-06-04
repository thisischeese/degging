from uuid import UUID
import unittest
from unittest.mock import patch

from app.services.discovery_service import (
    DiscoveryService,
    RecommendedCafe,
    _DISCOVERY_CAFE_QUERY,
)
from app.services.preference_vector import (
    USER_PREFERENCE_QUERY,
    InvalidPreferenceVectorError,
    UserPreferenceNotFoundError,
)


class FakeConnection:
    def __init__(self, rows_by_query):
        self._rows_by_query = rows_by_query
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    async def fetch(self, query, *args):
        self.calls.append((query, args))
        return self._rows_by_query.get(query, [])

    async def fetchrow(self, query, *args):
        self.calls.append((query, args))
        return self._rows_by_query.get(query)


class FakeAcquire:
    def __init__(self, connection):
        self._connection = connection

    async def __aenter__(self):
        return self._connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakePool:
    def __init__(self, rows_by_query):
        self._rows_by_query = rows_by_query
        self.last_connection: FakeConnection | None = None

    def acquire(self):
        self.last_connection = FakeConnection(self._rows_by_query)
        return FakeAcquire(self.last_connection)


class DiscoveryServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_discover_reads_preference_vector_from_postgresql(self) -> None:
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        first_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        second_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174002")
        pool = FakePool(
            {
                USER_PREFERENCE_QUERY: {"preference_vector": "[0.1,0.2,0.3,0.4]"},
                _DISCOVERY_CAFE_QUERY: [
                    {"cafe_id": str(first_cafe_id), "name": "Cafe Alpha"},
                    {"cafe_id": str(second_cafe_id), "name": "Cafe Beta"},
                ],
            }
        )
        service = DiscoveryService()

        with (
            patch("app.services.discovery_service.get_pg_pool", return_value=pool),
            patch("app.services.discovery_service.settings.discovery_top_k", 100),
            patch(
                "app.services.preference_vector.EXPECTED_PREFERENCE_VECTOR_DIMENSIONS",
                4,
            ),
        ):
            cafe_ids = await service.discover(user_id)

        self.assertEqual(
            cafe_ids,
            [
                RecommendedCafe(cafe_id=first_cafe_id, name="Cafe Alpha"),
                RecommendedCafe(cafe_id=second_cafe_id, name="Cafe Beta"),
            ],
        )
        self.assertIsNotNone(pool.last_connection)
        self.assertEqual(
            pool.last_connection.calls,
            [
                (USER_PREFERENCE_QUERY, (user_id,)),
                (_DISCOVERY_CAFE_QUERY, ("[0.1,0.2,0.3,0.4]", 100)),
            ],
        )

    async def test_get_top_cafes_by_vector_uses_requested_limit(self) -> None:
        cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        pool = FakePool(
            {
                _DISCOVERY_CAFE_QUERY: [
                    {"cafe_id": str(cafe_id), "name": "Cafe Gamma"},
                ]
            }
        )
        service = DiscoveryService()

        with patch("app.services.discovery_service.get_pg_pool", return_value=pool):
            cafes = await service.get_top_cafes_by_vector([0.1, 0.2, 0.3, 0.4], top_k=17)

        self.assertIsNotNone(pool.last_connection)
        _, args = pool.last_connection.calls[0]
        self.assertEqual(args, ("[0.1,0.2,0.3,0.4]", 17))
        self.assertEqual(
            cafes,
            [RecommendedCafe(cafe_id=cafe_id, name="Cafe Gamma")],
        )

    async def test_get_top_cafes_by_vector_normalizes_blank_name_to_none(self) -> None:
        cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        pool = FakePool(
            {
                _DISCOVERY_CAFE_QUERY: [
                    {"cafe_id": str(cafe_id), "name": "   "},
                ]
            }
        )
        service = DiscoveryService()

        with patch("app.services.discovery_service.get_pg_pool", return_value=pool):
            cafes = await service.get_top_cafes_by_vector([0.1, 0.2, 0.3, 0.4], top_k=1)

        self.assertEqual(
            cafes,
            [RecommendedCafe(cafe_id=cafe_id, name=None)],
        )

    async def test_get_top_cafes_by_vector_returns_empty_list_when_no_rows(self) -> None:
        pool = FakePool({_DISCOVERY_CAFE_QUERY: []})
        service = DiscoveryService()

        with patch("app.services.discovery_service.get_pg_pool", return_value=pool):
            cafes = await service.get_top_cafes_by_vector([0.1, 0.2, 0.3, 0.4], top_k=3)

        self.assertEqual(cafes, [])

    async def test_get_user_preference_vector_raises_404_when_missing(self) -> None:
        service = DiscoveryService()
        pool = FakePool({USER_PREFERENCE_QUERY: None})

        with (
            patch("app.services.discovery_service.get_pg_pool", return_value=pool),
            patch(
                "app.services.preference_vector.EXPECTED_PREFERENCE_VECTOR_DIMENSIONS",
                4,
            ),
        ):
            with self.assertRaises(UserPreferenceNotFoundError):
                await service.get_user_preference_vector(
                    UUID("123e4567-e89b-12d3-a456-426614174000")
                )

    async def test_get_user_preference_vector_raises_on_invalid_literal(self) -> None:
        service = DiscoveryService()
        pool = FakePool({USER_PREFERENCE_QUERY: {"preference_vector": "not-a-vector"}})

        with (
            patch("app.services.discovery_service.get_pg_pool", return_value=pool),
            patch(
                "app.services.preference_vector.EXPECTED_PREFERENCE_VECTOR_DIMENSIONS",
                4,
            ),
        ):
            with self.assertRaises(InvalidPreferenceVectorError):
                await service.get_user_preference_vector(
                    UUID("123e4567-e89b-12d3-a456-426614174000")
                )

    async def test_get_user_preference_vector_raises_on_dimension_mismatch(self) -> None:
        service = DiscoveryService()
        pool = FakePool({USER_PREFERENCE_QUERY: {"preference_vector": "[0.1,0.2]"}})

        with (
            patch("app.services.discovery_service.get_pg_pool", return_value=pool),
            patch(
                "app.services.preference_vector.EXPECTED_PREFERENCE_VECTOR_DIMENSIONS",
                4,
            ),
        ):
            with self.assertRaises(InvalidPreferenceVectorError):
                await service.get_user_preference_vector(
                    UUID("123e4567-e89b-12d3-a456-426614174000")
                )

    def test_discovery_query_filters_null_cafe_vectors(self) -> None:
        self.assertIn("WHERE cafe_vector IS NOT NULL", _DISCOVERY_CAFE_QUERY)

    def test_discovery_query_selects_cafe_name(self) -> None:
        self.assertIn("name", _DISCOVERY_CAFE_QUERY)
