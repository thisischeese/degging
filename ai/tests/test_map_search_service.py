import unittest
from uuid import UUID
from unittest.mock import patch

from app.models.map_search import MapSearchRequest
from app.services.map_search_service import (
    CafeCandidate,
    CafeMenu,
    MapSearchService,
    _CAFE_MENU_QUERY,
    _RADIUS_CAFE_QUERY,
    _USER_PREFERENCE_QUERY,
)
from app.services.preference_vector import UserPreferenceNotFoundError
from app.services.query_preprocess_service import PreprocessedQuery

QUIET_MOOD_ID = UUID("e747e844-db71-42ea-81cf-c25d510672b2")


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
    async def test_search_allows_blank_keyword_and_returns_ranked_cafes(self) -> None:
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _USER_PREFERENCE_QUERY: {"preference_vector": "[0.1,0.2,0.3]"},
                _RADIUS_CAFE_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "name": "Cafe A",
                        "address": "\uc11c\uc6b8\uc2dc \uc911\uad6c",
                        "road_address": None,
                        "cafe_intro": "\uc870\uc6a9\ud55c \ub514\uc800\ud2b8 \uce74\ud398",
                        "brand_name": None,
                        "branch_name": None,
                        "preference_similarity": 0.8,
                    }
                ],
                _CAFE_MENU_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "menu_id": 2394,
                        "menu_name": "Americano",
                        "menu_description": None,
                    }
                ],
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
                    keyword="   ",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertEqual(preprocess_service.calls, [""])
        self.assertEqual(response.cafes, {str(cafe_id): 1})
        self.assertEqual(response.extracted_menus, {})

    async def test_search_raises_when_user_preference_is_missing(self) -> None:
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )
        pool = FakePool({_USER_PREFERENCE_QUERY: None})

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
            with self.assertRaises(UserPreferenceNotFoundError):
                await service.search(
                    MapSearchRequest(
                        mood=[],
                        userId=UUID("123e4567-e89b-12d3-a456-426614174000"),
                        keyword="",
                        latitude=37.5665,
                        longitude=126.978,
                    )
                )

    async def test_get_candidates_within_radius_uses_2km_radius(self) -> None:
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )
        pool = FakePool({_RADIUS_CAFE_QUERY: []})

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
            await service.get_candidates_within_radius(
                latitude=37.5665,
                longitude=126.978,
                preference_vector=[0.1, 0.2, 0.3],
            )

        self.assertIsNotNone(pool.last_connection)
        _, args = pool.last_connection.calls[0]
        self.assertEqual(args[3], 2000)

    def test_rank_cafes_applies_mood_lexical_filter(self) -> None:
        quiet_cafe = UUID("123e4567-e89b-12d3-a456-426614174001")
        loud_cafe = UUID("123e4567-e89b-12d3-a456-426614174002")
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )

        ranked_cafes = service.rank_cafes(
            candidates=[
                CafeCandidate(
                    cafe_id=loud_cafe,
                    preference_similarity=0.99,
                    name="Loud Cafe",
                    address=None,
                    road_address=None,
                    cafe_intro="\ud65c\uae30\ucc2c \ubd84\uc704\uae30\uc758 \uce74\ud398",
                    brand_name=None,
                    branch_name=None,
                ),
                CafeCandidate(
                    cafe_id=quiet_cafe,
                    preference_similarity=0.80,
                    name="Quiet Cafe",
                    address=None,
                    road_address=None,
                    cafe_intro="\uc870\uc6a9\ud55c \ubd84\uc704\uae30\uc5d0\uc11c \uacf5\ubd80\ud558\uae30 \uc88b\uc740 \uce74\ud398",
                    brand_name=None,
                    branch_name=None,
                ),
            ],
            menus_by_cafe={},
            normalized_keyword="\uce74\ud398",
            mood_keywords=service.resolve_mood_keywords([QUIET_MOOD_ID]),
        )

        self.assertEqual(ranked_cafes, [quiet_cafe])

    def test_rank_cafes_sorts_by_vector_similarity_after_lexical_filter(self) -> None:
        higher_similarity = UUID("123e4567-e89b-12d3-a456-426614174001")
        lower_similarity = UUID("123e4567-e89b-12d3-a456-426614174002")
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )

        ranked_cafes = service.rank_cafes(
            candidates=[
                CafeCandidate(
                    cafe_id=lower_similarity,
                    preference_similarity=0.75,
                    name="Cafe B",
                    address=None,
                    road_address=None,
                    cafe_intro="\uc870\uc6a9\ud55c \uc870\uc6a9\ud55c \uac10\uc131 \uce74\ud398",
                    brand_name=None,
                    branch_name=None,
                ),
                CafeCandidate(
                    cafe_id=higher_similarity,
                    preference_similarity=0.95,
                    name="Cafe A",
                    address=None,
                    road_address=None,
                    cafe_intro="\uc870\uc6a9\ud55c \uac10\uc131 \uce74\ud398",
                    brand_name=None,
                    branch_name=None,
                ),
            ],
            menus_by_cafe={},
            normalized_keyword="\uac10\uc131",
            mood_keywords=service.resolve_mood_keywords([QUIET_MOOD_ID]),
        )

        self.assertEqual(ranked_cafes, [higher_similarity, lower_similarity])

    def test_resolve_extracted_menu_ids_uses_top_ranked_cafe_menu_id(self) -> None:
        top_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        lower_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174002")
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )

        extracted_menus = service.resolve_extracted_menu_ids(
            normalized_query="Americano Americano",
            menu_phrases=[],
            menus_by_cafe={
                top_cafe_id: [
                    CafeMenu(
                        cafe_id=top_cafe_id,
                        menu_id=2394,
                        menu_name="Americano",
                        menu_description=None,
                    )
                ],
                lower_cafe_id: [
                    CafeMenu(
                        cafe_id=lower_cafe_id,
                        menu_id=10209,
                        menu_name="Americano",
                        menu_description=None,
                    )
                ],
            },
            ranked_cafe_ids=[top_cafe_id, lower_cafe_id],
        )

        self.assertEqual(extracted_menus, {"2394": 2})

    def test_search_result_is_trimmed_to_top_100(self) -> None:
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )
        candidates = [
            CafeCandidate(
                cafe_id=UUID(f"00000000-0000-0000-0000-{index:012d}"),
                preference_similarity=1.0 - (index / 1000.0),
                name=f"Cafe {index}",
                address=None,
                road_address=None,
                cafe_intro="\uc870\uc6a9\ud55c \uac10\uc131 \uce74\ud398",
                brand_name=None,
                branch_name=None,
            )
            for index in range(101)
        ]

        ranked_cafes = service.rank_cafes(
            candidates=candidates,
            menus_by_cafe={},
            normalized_keyword="\uac10\uc131",
            mood_keywords=service.resolve_mood_keywords([QUIET_MOOD_ID]),
        )
        cafes = {
            str(cafe_id): rank
            for rank, cafe_id in enumerate(ranked_cafes[:100], start=1)
        }

        self.assertEqual(len(cafes), 100)
