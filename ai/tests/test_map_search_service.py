import unittest
from uuid import UUID
from unittest.mock import patch

from app.models.map_search import MapSearchRequest
from app.services.map_search_service import (
    CafeCandidate,
    MapSearchService,
    MenuSearchHit,
    _CANDIDATE_MENU_SEARCH_FUSED_QUERY,
    _CANDIDATE_MENU_SEARCH_KEYWORD_ONLY_QUERY,
    _RADIUS_MOOD_CAFE_QUERY,
)
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
        self.connections: list[FakeConnection] = []

    def acquire(self):
        self.last_connection = FakeConnection(self._rows_by_query)
        self.connections.append(self.last_connection)
        return FakeAcquire(self.last_connection)


class StubPreprocessService:
    def __init__(
        self,
        processed_query: PreprocessedQuery,
        *,
        query_vector: list[float] | None = None,
    ) -> None:
        self._processed_query = processed_query
        self._query_vector = query_vector or []
        self.preprocess_calls: list[str] = []
        self.encode_calls: list[str] = []

    async def preprocess(self, query: str) -> PreprocessedQuery:
        self.preprocess_calls.append(query)
        return self._processed_query

    async def encode_query(self, query: str) -> list[float]:
        self.encode_calls.append(query)
        return list(self._query_vector)


class MapSearchServiceTest(unittest.IsolatedAsyncioTestCase):
    def test_rrf_queries_cast_window_ranks_to_integer(self) -> None:
        self.assertIn("))::integer AS keyword_rank", _CANDIDATE_MENU_SEARCH_FUSED_QUERY)
        self.assertIn("))::integer AS dense_rank", _CANDIDATE_MENU_SEARCH_FUSED_QUERY)
        self.assertIn("$6::integer", _CANDIDATE_MENU_SEARCH_FUSED_QUERY)
        self.assertIn("))::integer AS keyword_rank", _CANDIDATE_MENU_SEARCH_KEYWORD_ONLY_QUERY)
        self.assertIn("$5::integer", _CANDIDATE_MENU_SEARCH_KEYWORD_ONLY_QUERY)

    async def test_search_returns_empty_when_no_menu_phrases_are_extracted(self) -> None:
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(normalized_query="americano", menu_phrases=[])
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)

        response = await service.search(
            MapSearchRequest(
                mood=[],
                userId=UUID("123e4567-e89b-12d3-a456-426614174000"),
                keyword="americano",
                latitude=37.5665,
                longitude=126.978,
            )
        )

        self.assertEqual(preprocess_service.preprocess_calls, ["americano"])
        self.assertEqual(preprocess_service.encode_calls, [])
        self.assertEqual(response.cafes, {})
        self.assertEqual(response.extracted_menus, [])

    async def test_search_preserves_extracted_phrases_when_no_candidates_exist(self) -> None:
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="cake coffee",
                menu_phrases=["cake", "coffee"],
            ),
            query_vector=[0.1, 0.2, 0.3],
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool({_RADIUS_MOOD_CAFE_QUERY: []})

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
            response = await service.search(
                MapSearchRequest(
                    mood=[],
                    userId=UUID("123e4567-e89b-12d3-a456-426614174000"),
                    keyword="cake coffee",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertEqual(response.cafes, {})
        self.assertEqual(response.extracted_menus, ["cake", "coffee"])
        self.assertEqual(preprocess_service.encode_calls, [])

    async def test_search_ranks_candidates_by_best_rrf_hit(self) -> None:
        quiet_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        view_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174002")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="sunny cake",
                menu_phrases=["cake"],
            ),
            query_vector=[0.1, 0.2, 0.3],
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _RADIUS_MOOD_CAFE_QUERY: [
                    {
                        "cafe_id": str(view_cafe_id),
                        "name": "View Cafe",
                        "address": "Seoul",
                        "road_address": None,
                        "cafe_intro": "Bright brunch cafe",
                        "brand_name": None,
                        "branch_name": None,
                    },
                    {
                        "cafe_id": str(quiet_cafe_id),
                        "name": "Quiet Cafe",
                        "address": "Seoul",
                        "road_address": None,
                        "cafe_intro": "Calm dessert cafe",
                        "brand_name": None,
                        "branch_name": None,
                    },
                ],
                _CANDIDATE_MENU_SEARCH_FUSED_QUERY: [
                    {
                        "cafe_id": str(view_cafe_id),
                        "menu_id": 10,
                        "menu_name": "Strawberry Cake",
                        "menu_description": "Fresh cake",
                        "keyword_rank": 2,
                        "dense_rank": 2,
                        "rrf_score": 0.032258,
                    },
                    {
                        "cafe_id": str(quiet_cafe_id),
                        "menu_id": 20,
                        "menu_name": "Butter Cake",
                        "menu_description": "Soft cake",
                        "keyword_rank": 1,
                        "dense_rank": 1,
                        "rrf_score": 0.032787,
                    },
                ],
            }
        )

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
            response = await service.search(
                MapSearchRequest(
                    mood=[UUID("e747e844-db71-42ea-81cf-c25d510672b2")],
                    userId=UUID("123e4567-e89b-12d3-a456-426614174000"),
                    keyword="sunny cake",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertEqual(preprocess_service.encode_calls, ["sunny cake"])
        self.assertEqual(response.extracted_menus, ["cake"])
        self.assertEqual(response.cafes, {str(quiet_cafe_id): 1, str(view_cafe_id): 2})

    async def test_search_falls_back_to_keyword_only_when_query_vector_is_empty(self) -> None:
        cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="cream latte",
                menu_phrases=["latte"],
            ),
            query_vector=[],
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _RADIUS_MOOD_CAFE_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "name": "Latte Cafe",
                        "address": "Seoul",
                        "road_address": None,
                        "cafe_intro": "Creamy menu",
                        "brand_name": None,
                        "branch_name": None,
                    }
                ],
                _CANDIDATE_MENU_SEARCH_KEYWORD_ONLY_QUERY: [
                    {
                        "cafe_id": str(cafe_id),
                        "menu_id": 3,
                        "menu_name": "Cream Latte",
                        "menu_description": "Smooth milk foam",
                        "keyword_rank": 1,
                        "dense_rank": None,
                        "rrf_score": 0.016393,
                    }
                ],
            }
        )

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
            response = await service.search(
                MapSearchRequest(
                    mood=[],
                    userId=UUID("123e4567-e89b-12d3-a456-426614174000"),
                    keyword="cream latte",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertEqual(response.cafes, {str(cafe_id): 1})
        self.assertEqual(len(pool.connections), 2)
        self.assertEqual(pool.connections[1].calls[0][0], _CANDIDATE_MENU_SEARCH_KEYWORD_ONLY_QUERY)

    async def test_get_candidates_within_radius_uses_2km_radius_and_mood_ids(self) -> None:
        service = MapSearchService(
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="cake", menu_phrases=["cake"])
            )
        )
        quiet_mood = UUID("e747e844-db71-42ea-81cf-c25d510672b2")
        pool = FakePool({_RADIUS_MOOD_CAFE_QUERY: []})

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
            await service.get_candidates_within_radius(
                latitude=37.5665,
                longitude=126.978,
                mood_ids=[quiet_mood],
            )

        self.assertIsNotNone(pool.last_connection)
        _, args = pool.last_connection.calls[0]
        self.assertEqual(args[0], 126.978)
        self.assertEqual(args[1], 37.5665)
        self.assertEqual(args[2], 2000)
        self.assertEqual(args[3], [quiet_mood])

    async def test_search_uses_full_query_for_dense_encoding_and_sparse_phrase_query(self) -> None:
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="sunny butter cake",
                menu_phrases=["Butter Cake", "cake"],
            ),
            query_vector=[0.1, 0.2, 0.3],
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _RADIUS_MOOD_CAFE_QUERY: [
                    {
                        "cafe_id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "Cake Cafe",
                        "address": "Seoul",
                        "road_address": None,
                        "cafe_intro": "Dessert cafe",
                        "brand_name": None,
                        "branch_name": None,
                    }
                ],
                _CANDIDATE_MENU_SEARCH_FUSED_QUERY: [],
            }
        )

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
            await service.search(
                MapSearchRequest(
                    mood=[],
                    userId=UUID("123e4567-e89b-12d3-a456-426614174000"),
                    keyword="sunny butter cake",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertEqual(preprocess_service.encode_calls, ["sunny butter cake"])
        self.assertEqual(len(pool.connections), 2)
        query, args = pool.connections[1].calls[0]
        self.assertEqual(query, _CANDIDATE_MENU_SEARCH_FUSED_QUERY)
        self.assertEqual(args[1], "butter cake cake")
        self.assertEqual(args[3], "cafe_menus_menu_search_bm25_idx")

    def test_rank_cafes_uses_best_hit_per_cafe_and_cafe_id_tiebreaker(self) -> None:
        service = MapSearchService()
        first_cafe = UUID("123e4567-e89b-12d3-a456-426614174001")
        second_cafe = UUID("123e4567-e89b-12d3-a456-426614174002")

        ranked_cafes = service.rank_cafes(
            [
                MenuSearchHit(
                    cafe_id=second_cafe,
                    menu_id=20,
                    menu_name="Cake",
                    menu_description=None,
                    keyword_rank=1,
                    dense_rank=2,
                    rrf_score=0.032,
                ),
                MenuSearchHit(
                    cafe_id=first_cafe,
                    menu_id=10,
                    menu_name="Cake",
                    menu_description=None,
                    keyword_rank=1,
                    dense_rank=2,
                    rrf_score=0.032,
                ),
                MenuSearchHit(
                    cafe_id=first_cafe,
                    menu_id=11,
                    menu_name="Cake Special",
                    menu_description=None,
                    keyword_rank=3,
                    dense_rank=3,
                    rrf_score=0.031,
                ),
            ]
        )

        self.assertEqual(ranked_cafes, [first_cafe, second_cafe])

    async def test_search_logs_updated_flow_events(self) -> None:
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(
                normalized_query="cake",
                menu_phrases=["cake"],
            ),
            query_vector=[0.1, 0.2, 0.3],
        )
        service = MapSearchService(query_preprocess_service=preprocess_service)
        pool = FakePool(
            {
                _RADIUS_MOOD_CAFE_QUERY: [
                    {
                        "cafe_id": "123e4567-e89b-12d3-a456-426614174001",
                        "name": "Cafe A",
                        "address": "Seoul",
                        "road_address": None,
                        "cafe_intro": "Quiet dessert cafe",
                        "brand_name": None,
                        "branch_name": None,
                    }
                ],
                _CANDIDATE_MENU_SEARCH_FUSED_QUERY: [
                    {
                        "cafe_id": "123e4567-e89b-12d3-a456-426614174001",
                        "menu_id": 1,
                        "menu_name": "Chocolate Cake",
                        "menu_description": "Sweet dessert",
                        "keyword_rank": 1,
                        "dense_rank": 1,
                        "rrf_score": 0.032787,
                    }
                ],
            }
        )

        with (
            patch("app.services.map_search_service.get_pg_pool", return_value=pool),
            self.assertLogs("uvicorn.error", level="INFO") as logs,
        ):
            await service.search(
                MapSearchRequest(
                    mood=[],
                    userId=UUID("123e4567-e89b-12d3-a456-426614174000"),
                    keyword="cake",
                    latitude=37.5665,
                    longitude=126.978,
                )
            )

        self.assertTrue(any("map_search_menu_list_completed" in message for message in logs.output))
        self.assertTrue(any("map_search_candidates_filtered" in message for message in logs.output))
        self.assertTrue(any("map_search_menu_lookup_completed" in message for message in logs.output))
        self.assertTrue(any("map_search_ranking_completed" in message for message in logs.output))
