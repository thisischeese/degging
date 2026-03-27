import unittest
from uuid import UUID
from unittest.mock import patch

from app.models.map_search import MapSearchRequest
from app.services.map_search_service import (
    CafeCandidate,
    CafeMenu,
    MapSearchService,
    _CAFE_MENU_QUERY,
    _CAFE_MENU_SEARCH_FUSED_QUERY,
    _CAFE_MENU_SEARCH_KEYWORD_ONLY_QUERY,
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
                        "address": "서울시 중구",
                        "road_address": None,
                        "cafe_intro": "조용한 디저트 카페",
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
                        "menu_search_text": "Americano",
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

    async def test_search_resolves_menu_ids_with_rrf_hits(self) -> None:
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        top_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        lower_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174002")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="아메리카노",
                vector=[0.1] * 64,
                menu_phrases=["아메리카노"],
                phrase_vectors={"아메리카노": [0.1] * 64},
            )
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _USER_PREFERENCE_QUERY: {"preference_vector": "[0.1,0.2,0.3]"},
                _RADIUS_CAFE_QUERY: [
                    {
                        "cafe_id": str(top_cafe_id),
                        "name": "Cafe A",
                        "address": "서울시 중구",
                        "road_address": None,
                        "cafe_intro": "조용한 아메리카노 카페",
                        "brand_name": None,
                        "branch_name": None,
                        "preference_similarity": 0.8,
                    },
                    {
                        "cafe_id": str(lower_cafe_id),
                        "name": "Cafe B",
                        "address": "서울시 중구",
                        "road_address": None,
                        "cafe_intro": "아메리카노 전문 카페",
                        "brand_name": None,
                        "branch_name": None,
                        "preference_similarity": 0.7,
                    },
                ],
                _CAFE_MENU_QUERY: [
                    {
                        "cafe_id": str(top_cafe_id),
                        "menu_id": 2394,
                        "menu_name": "아이스 아메리카노",
                        "menu_description": "시원한 아메리카노",
                        "menu_search_text": "아이스 아메리카노 시원한 아메리카노",
                    },
                    {
                        "cafe_id": str(lower_cafe_id),
                        "menu_id": 10209,
                        "menu_name": "뜨거운 아메리카노",
                        "menu_description": None,
                        "menu_search_text": "뜨거운 아메리카노",
                    },
                ],
                _CAFE_MENU_SEARCH_FUSED_QUERY: [
                    {
                        "cafe_id": str(top_cafe_id),
                        "menu_id": 2394,
                        "menu_name": "아이스 아메리카노",
                        "menu_description": "시원한 아메리카노",
                        "keyword_rank": 1,
                        "vector_rank": 1,
                        "rrf_score": 0.0327868852459,
                    },
                    {
                        "cafe_id": str(lower_cafe_id),
                        "menu_id": 10209,
                        "menu_name": "뜨거운 아메리카노",
                        "menu_description": None,
                        "keyword_rank": 2,
                        "vector_rank": 2,
                        "rrf_score": 0.0322580645161,
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
                    mood=[],
                    userId=user_id,
                    keyword="아메리카노",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertEqual(response.extracted_menus, {"2394": 1})
        self.assertEqual(response.cafes, {str(top_cafe_id): 1, str(lower_cafe_id): 2})

    async def test_search_logs_info_events(self) -> None:
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="아메리카노",
                vector=[0.1] * 64,
                menu_phrases=["아메리카노"],
                phrase_vectors={"아메리카노": [0.1] * 64},
            )
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _USER_PREFERENCE_QUERY: {"preference_vector": "[0.1,0.2,0.3]"},
                _RADIUS_CAFE_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "name": "Cafe A",
                        "address": "서울시 중구",
                        "road_address": None,
                        "cafe_intro": "조용한 아메리카노 카페",
                        "brand_name": None,
                        "branch_name": None,
                        "preference_similarity": 0.8,
                    }
                ],
                _CAFE_MENU_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "menu_id": 2394,
                        "menu_name": "아이스 아메리카노",
                        "menu_description": None,
                        "menu_search_text": "아이스 아메리카노",
                    }
                ],
                _CAFE_MENU_SEARCH_FUSED_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "menu_id": 2394,
                        "menu_name": "아이스 아메리카노",
                        "menu_description": None,
                        "keyword_rank": 1,
                        "vector_rank": 1,
                        "rrf_score": 0.0327868852459,
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
                    keyword="아메리카노",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertTrue(any("map_search_started" in message for message in logs.output))
        self.assertTrue(any("map_search_menu_lookup_completed" in message for message in logs.output))
        self.assertTrue(any("map_search_menu_selected" in message for message in logs.output))
        self.assertTrue(any("map_search_menu_rrf_completed" in message for message in logs.output))
        self.assertTrue(any("map_search_ranking_completed" in message for message in logs.output))

    async def test_search_uses_keyword_only_menu_query_without_phrase_vector(self) -> None:
        user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
        cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="americano",
                vector=[],
                menu_phrases=["americano"],
                phrase_vectors={"americano": []},
                used_query_fallback=True,
            )
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _USER_PREFERENCE_QUERY: {"preference_vector": "[0.1,0.2,0.3]"},
                _RADIUS_CAFE_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "name": "Cafe A",
                        "address": "Seoul",
                        "road_address": None,
                        "cafe_intro": "Quiet coffee bar",
                        "brand_name": None,
                        "branch_name": None,
                        "preference_similarity": 0.8,
                    }
                ],
                _CAFE_MENU_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "menu_id": 2394,
                        "menu_name": "Iced Americano",
                        "menu_description": "Cold americano",
                        "menu_search_text": "Iced Americano Cold americano",
                    }
                ],
                _CAFE_MENU_SEARCH_KEYWORD_ONLY_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "menu_id": 2394,
                        "menu_name": "Iced Americano",
                        "menu_description": "Cold americano",
                        "keyword_rank": 1,
                        "vector_rank": None,
                        "rrf_score": 0.016393442623,
                    }
                ],
            }
        )

        with (
            patch("app.services.map_search_service.get_pg_pool", return_value=pool),
            patch("app.services.preference_vector.EXPECTED_PREFERENCE_VECTOR_DIMENSIONS", 3),
            self.assertLogs("uvicorn.error", level="INFO") as logs,
        ):
            response = await service.search(
                MapSearchRequest(
                    mood=[],
                    userId=user_id,
                    keyword="americano",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertEqual(response.extracted_menus, {"2394": 1})
        self.assertEqual(response.cafes, {str(cafe_id): 1})
        self.assertTrue(
            any("map_search_menu_resolution_completed" in message and "used_query_fallback=True" in message for message in logs.output)
        )

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
                    cafe_intro="활기찬 분위기의 카페",
                    brand_name=None,
                    branch_name=None,
                ),
                CafeCandidate(
                    cafe_id=quiet_cafe,
                    preference_similarity=0.80,
                    name="Quiet Cafe",
                    address=None,
                    road_address=None,
                    cafe_intro="조용한 분위기에서 공부하기 좋은 카페",
                    brand_name=None,
                    branch_name=None,
                ),
            ],
            menus_by_cafe={},
            normalized_keyword="카페",
            mood_keywords=service.resolve_mood_keywords([QUIET_MOOD_ID]),
        )

        self.assertEqual(ranked_cafes, [quiet_cafe])

    def test_rank_cafes_prefers_menu_scores_when_present(self) -> None:
        higher_similarity = UUID("123e4567-e89b-12d3-a456-426614174001")
        menu_match = UUID("123e4567-e89b-12d3-a456-426614174002")
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )

        ranked_cafes = service.rank_cafes(
            candidates=[
                CafeCandidate(
                    cafe_id=higher_similarity,
                    preference_similarity=0.95,
                    name="Cafe A",
                    address=None,
                    road_address=None,
                    cafe_intro="감성 카페",
                    brand_name=None,
                    branch_name=None,
                ),
                CafeCandidate(
                    cafe_id=menu_match,
                    preference_similarity=0.50,
                    name="Cafe B",
                    address=None,
                    road_address=None,
                    cafe_intro="감성 카페",
                    brand_name=None,
                    branch_name=None,
                ),
            ],
            menus_by_cafe={},
            normalized_keyword="",
            residual_keyword="",
            mood_keywords=[],
            menu_scores_by_cafe={menu_match: 0.9},
        )

        self.assertEqual(ranked_cafes, [menu_match])

    def test_collect_menu_phrase_counts_prefers_query_occurrence_count(self) -> None:
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )

        counts = service.collect_menu_phrase_counts(
            normalized_query="Americano Americano",
            menu_phrases=["Americano"],
        )

        self.assertEqual(counts["Americano"], 2)

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
                cafe_intro="조용한 감성 카페",
                brand_name=None,
                branch_name=None,
            )
            for index in range(101)
        ]

        ranked_cafes = service.rank_cafes(
            candidates=candidates,
            menus_by_cafe={},
            normalized_keyword="감성",
            mood_keywords=service.resolve_mood_keywords([QUIET_MOOD_ID]),
        )
        cafes = {
            str(cafe_id): rank
            for rank, cafe_id in enumerate(ranked_cafes[:100], start=1)
        }

        self.assertEqual(len(cafes), 100)
