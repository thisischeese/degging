from uuid import UUID
import unittest
from unittest.mock import patch

from app.models.map_search import MapSearchRequest
from app.services.discovery_service import UserPreferenceNotFoundError
from app.services.map_search_service import CafeCandidate, CafeMenu, MapSearchService
from app.services.map_search_service import _CAFE_MENU_QUERY, _RADIUS_CAFE_QUERY
from app.services.query_preprocess_service import PreprocessedQuery


class FakeCollection:
    def __init__(self, document):
        self._document = document

    async def find_one(self, *args, **kwargs):
        return self._document


class FakeMongoDatabase:
    def __init__(self, document):
        self._document = document

    def __getitem__(self, name):
        return FakeCollection(self._document)


class FakeConnection:
    def __init__(self, rows_by_query):
        self._rows_by_query = rows_by_query
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    async def fetch(self, query, *args):
        self.calls.append((query, args))
        return self._rows_by_query[query]


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
        mongo_db = FakeMongoDatabase({"u_rt": [0.1, 0.2, 0.3]})
        preprocess_service = StubPreprocessService(
            PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
        )
        service = MapSearchService(
            mongo_db,
            query_preprocess_service=preprocess_service,
        )
        pool = FakePool(
            {
                _RADIUS_CAFE_QUERY: [
                    {"cafe_id": str(cafe_id), "preference_similarity": 0.8}
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

        with patch("app.services.map_search_service.get_pg_pool", return_value=pool):
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
            FakeMongoDatabase(None),
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )

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
            FakeMongoDatabase({"u_rt": [0.1, 0.2, 0.3]}),
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

    def test_score_cafe_menus_handles_null_description(self) -> None:
        service = MapSearchService(
            FakeMongoDatabase({"u_rt": [0.1, 0.2, 0.3]}),
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )

        score = service.score_cafe_menus(
            ["americano"],
            [
                CafeMenu(
                    cafe_id=UUID("123e4567-e89b-12d3-a456-426614174001"),
                    menu_id=1,
                    menu_name="Americano",
                    menu_description=None,
                )
            ],
        )

        self.assertGreater(score, 0.0)

    def test_resolve_extracted_menu_ids_uses_top_ranked_cafe_menu_id(self) -> None:
        top_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        lower_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174002")
        service = MapSearchService(
            FakeMongoDatabase({"u_rt": [0.1, 0.2, 0.3]}),
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

    def test_rank_cafes_orders_by_final_score(self) -> None:
        top_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174001")
        lower_cafe_id = UUID("123e4567-e89b-12d3-a456-426614174002")
        service = MapSearchService(
            FakeMongoDatabase({"u_rt": [0.1, 0.2, 0.3]}),
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )

        ranked_cafes = service.rank_cafes(
            candidates=[
                CafeCandidate(cafe_id=lower_cafe_id, preference_similarity=0.2),
                CafeCandidate(cafe_id=top_cafe_id, preference_similarity=0.9),
            ],
            menus_by_cafe={},
            normalized_keyword="",
            mood_keywords=[],
            query_similarity_scores={},
        )

        self.assertEqual(ranked_cafes, [top_cafe_id, lower_cafe_id])

    def test_search_result_is_trimmed_to_top_100(self) -> None:
        service = MapSearchService(
            FakeMongoDatabase({"u_rt": [0.1, 0.2, 0.3]}),
            query_preprocess_service=StubPreprocessService(
                PreprocessedQuery(normalized_query="", vector=[], menu_phrases=[])
            ),
        )
        candidates = [
            CafeCandidate(
                cafe_id=UUID(f"00000000-0000-0000-0000-{index:012d}"),
                preference_similarity=1.0 - (index / 1000.0),
            )
            for index in range(101)
        ]

        ranked_cafes = service.rank_cafes(
            candidates=candidates,
            menus_by_cafe={},
            normalized_keyword="",
            mood_keywords=[],
            query_similarity_scores={},
        )
        cafes = {
            str(cafe_id): rank
            for rank, cafe_id in enumerate(ranked_cafes[:100], start=1)
        }

        self.assertEqual(len(cafes), 100)
