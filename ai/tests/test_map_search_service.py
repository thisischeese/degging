import unittest
from uuid import UUID
from unittest.mock import patch

from app.models.map_search import MapSearchRequest
from app.services.map_search_service import (
    CafeCandidate,
    CafeMenu,
    MapSearchService,
    _CAFE_MENU_QUERY,
    _RADIUS_MENU_CAFE_QUERY,
    _USER_PREFERENCE_QUERY,
)
from app.services.preference_vector import UserPreferenceNotFoundError
from app.services.query_preprocess_service import PreprocessedQuery


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


class StubPreprocessService:
    def __init__(self, processed_query: PreprocessedQuery):
        self._processed_query = processed_query
        self.calls: list[str] = []

    async def preprocess(self, query: str) -> PreprocessedQuery:
        self.calls.append(query)
        return self._processed_query


class MapSearchServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_search_returns_empty_when_no_menu_phrases_are_extracted(self) -> None:
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(normalized_query="americano", menu_phrases=[])
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)

        response = await service.search(
            MapSearchRequest(
                mood=[],
                userId=user_id,
                keyword="americano",
                latitude=37.5665,
                longitude=126.978,
            )
        )

        self.assertEqual(preprocess_service.calls, ["americano"])
        self.assertEqual(response.cafes, {})
        self.assertEqual(response.extracted_menus, [])

    async def test_search_preserves_extracted_phrases_when_no_candidates_exist(self) -> None:
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="cake coffee",
                menu_phrases=["cake", "coffee"],
            )
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _USER_PREFERENCE_QUERY: {"preference_vector": "[0.1,0.2,0.3]"},
                _RADIUS_MENU_CAFE_QUERY: [],
            }
        )

        with (
            patch("app.services.map_search_service.get_pg_pool", return_value=pool),
            patch("app.services.preference_vector.EXPECTED_PREFERENCE_VECTOR_DIMENSIONS", 3),
        ):
            response = await service.search(
                MapSearchRequest(
                    mood=[],
                    userId=user_id,
                    keyword="cake coffee",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertEqual(response.cafes, {})
        self.assertEqual(response.extracted_menus, ["cake", "coffee"])

    async def test_search_ranks_candidates_by_vector_similarity_then_mood(self) -> None:
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        quiet_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        loud_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174002")
        quiet_mood = UUID("e747e844-db71-42ea-81cf-c25d510672b2")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="cake",
                menu_phrases=["cake"],
            )
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _USER_PREFERENCE_QUERY: {"preference_vector": "[0.1,0.2,0.3]"},
                _RADIUS_MENU_CAFE_QUERY: [
                    {
                        "cafe_id": str(loud_cafe_id),
                        "name": "Loud Cafe",
                        "address": "Seoul",
                        "road_address": None,
                        "cafe_intro": "Bright dessert cafe",
                        "brand_name": None,
                        "branch_name": None,
                        "matched_phrase_count": 1,
                        "preference_similarity": 0.8,
                    },
                    {
                        "cafe_id": str(quiet_cafe_id),
                        "name": "Quiet Cafe",
                        "address": "Seoul",
                        "road_address": None,
                        "cafe_intro": "Quiet calm dessert cafe",
                        "brand_name": None,
                        "branch_name": None,
                        "matched_phrase_count": 1,
                        "preference_similarity": 0.8,
                    },
                ],
                _CAFE_MENU_QUERY: [
                    {
                        "cafe_id": str(loud_cafe_id),
                        "menu_id": 1,
                        "menu_name": "Chocolate Cake",
                        "menu_description": "Sweet dessert",
                    },
                    {
                        "cafe_id": str(quiet_cafe_id),
                        "menu_id": 2,
                        "menu_name": "Chocolate Cake",
                        "menu_description": "Sweet dessert",
                    },
                ],
            }
        )

        with (
            patch("app.services.map_search_service.get_pg_pool", return_value=pool),
            patch("app.services.preference_vector.EXPECTED_PREFERENCE_VECTOR_DIMENSIONS", 3),
        ):
            response = await service.search(
                MapSearchRequest(
                    mood=[quiet_mood],
                    userId=user_id,
                    keyword="cake",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertEqual(response.extracted_menus, ["cake"])
        self.assertEqual(response.cafes, {str(quiet_cafe_id): 1, str(loud_cafe_id): 2})

    async def test_search_raises_when_user_preference_is_missing(self) -> None:
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="cake", menu_phrases=["cake"])
            ),
        )
        pool = FakePool({_USER_PREFERENCE_QUERY: None})

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
            with self.assertRaises(UserPreferenceNotFoundError):
                await service.search(
                    MapSearchRequest(
                        mood=[],
                        userId=UUID("123e4567-e89b-12d3-a456-426614174000"),
                        keyword="cake",
                        latitude=37.5665,
                        longitude=126.978,
                    )
                )

    async def test_get_candidates_within_radius_uses_2km_radius_and_menu_phrases(self) -> None:
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="cake", menu_phrases=["cake"])
            ),
        )
        pool = FakePool({_RADIUS_MENU_CAFE_QUERY: []})

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
            await service.get_candidates_within_radius(
                latitude=37.5665,
                longitude=126.978,
                preference_vector=[0.1, 0.2, 0.3],
                menu_phrases=["cake", "coffee"],
            )

        self.assertIsNotNone(pool.last_connection)
        _, args = pool.last_connection.calls[0]
        self.assertEqual(args[3], 2000)
        self.assertEqual(args[4], ["cake", "coffee"])

    def test_rank_cafes_keeps_non_matching_mood_cafes_and_uses_mood_as_secondary(self) -> None:
        quiet_cafe = UUID("123e4567-e89b-12d3-a456-426614174001")
        plain_cafe = UUID("123e4567-e89b-12d3-a456-426614174002")
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="cake", menu_phrases=["cake"])
            ),
        )

        ranked_cafes = service.rank_cafes(
            candidates=[
                CafeCandidate(
                    cafe_id=plain_cafe,
                    preference_similarity=0.9,
                    matched_phrase_count=1,
                    name="Plain Cafe",
                    address=None,
                    road_address=None,
                    cafe_intro="Dessert cafe",
                    brand_name=None,
                    branch_name=None,
                ),
                CafeCandidate(
                    cafe_id=quiet_cafe,
                    preference_similarity=0.9,
                    matched_phrase_count=1,
                    name="Quiet Cafe",
                    address=None,
                    road_address=None,
                    cafe_intro="Quiet dessert cafe",
                    brand_name=None,
                    branch_name=None,
                ),
            ],
            menus_by_cafe={},
            mood_keywords=["quiet"],
        )

        self.assertEqual(ranked_cafes, [quiet_cafe, plain_cafe])

    async def test_search_logs_updated_flow_events(self) -> None:
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="cake",
                menu_phrases=["cake"],
            )
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _USER_PREFERENCE_QUERY: {"preference_vector": "[0.1,0.2,0.3]"},
                _RADIUS_MENU_CAFE_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "name": "Cafe A",
                        "address": "Seoul",
                        "road_address": None,
                        "cafe_intro": "Quiet dessert cafe",
                        "brand_name": None,
                        "branch_name": None,
                        "matched_phrase_count": 1,
                        "preference_similarity": 0.8,
                    }
                ],
                _CAFE_MENU_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "menu_id": 1,
                        "menu_name": "Chocolate Cake",
                        "menu_description": "Sweet dessert",
                    }
                ],
            }
        )

        with (
            patch("app.services.map_search_service.get_pg_pool", return_value=pool),
            patch("app.services.preference_vector.EXPECTED_PREFERENCE_VECTOR_DIMENSIONS", 3),
            self.assertLogs("uvicorn.error", level="INFO") as logs,
        ):
            await service.search(
                MapSearchRequest(
                    mood=[],
                    userId=user_id,
                    keyword="cake",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertTrue(any("map_search_menu_list_completed" in message for message in logs.output))
        self.assertTrue(any("map_search_candidates_loaded" in message for message in logs.output))
        self.assertTrue(any("map_search_ranking_completed" in message for message in logs.output))
        self.assertFalse(any("map_search_menu_resolution_completed" in message for message in logs.output))
