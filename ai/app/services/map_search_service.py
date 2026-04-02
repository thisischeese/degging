from __future__ import annotations

from dataclasses import dataclass
import logging
from uuid import UUID

from app.core.config import settings
from app.core.metrics import track_map_search_stage
from app.db.postgresql import get_pg_pool
from app.models.map_search import MapSearchRequest, MapSearchResponse
from app.services.preference_vector import to_vector_literal as to_shared_vector_literal
from app.services.query_preprocess_service import QueryPreprocessService

logger = logging.getLogger("uvicorn.error")

_RADIUS_METERS = 2000
_MAX_RESULTS = settings.discovery_top_k
_MENU_SEARCH_BM25_INDEX = "cafe_menus_menu_search_bm25_idx"
_MENU_SEARCH_LIMIT = 20
_MENU_LOG_LIMIT = 5
_MENU_NAME_LOG_LIMIT = 80
_RRF_K = 60
_DEFAULT_RANK = 2147483647

_RADIUS_MOOD_CAFE_QUERY = """
    SELECT
        cafe.cafe_id,
        cafe.name,
        cafe.address,
        cafe.road_address,
        cafe.cafe_intro,
        cafe.brand_name,
        cafe.branch_name
    FROM cafes AS cafe
    WHERE ST_DWithin(
              cafe.location,
              ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
              $3
          )
      AND (
              COALESCE(array_length($4::uuid[], 1), 0) = 0
              OR EXISTS (
                  SELECT 1
                  FROM cafe_vibe_tags AS vibe
                  WHERE vibe.cafe_id = cafe.cafe_id
                    AND vibe.tag_id = ANY($4::uuid[])
              )
          )
    ORDER BY cafe.name, cafe.cafe_id
"""

_CANDIDATE_MENU_SEARCH_FUSED_QUERY = """
    WITH candidate_cafes AS (
        SELECT UNNEST($1::uuid[]) AS cafe_id
    ),
    scored_keyword_hits AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            menu.menu_search_text <@> to_bm25query($2, $4) AS keyword_distance
        FROM cafe_menus AS menu
        JOIN candidate_cafes AS candidate
          ON candidate.cafe_id = menu.cafe_id
        WHERE COALESCE(menu.menu_search_text, '') <> ''
    ),
    ranked_keyword_hits AS (
        SELECT
            cafe_id,
            menu_id,
            keyword_distance,
            (ROW_NUMBER() OVER (
                ORDER BY keyword_distance ASC, menu_id, cafe_id
            ))::integer AS keyword_rank
        FROM scored_keyword_hits
    ),
    keyword_hits AS (
        SELECT
            cafe_id,
            menu_id,
            keyword_rank
        FROM ranked_keyword_hits
        WHERE keyword_rank <= $5
          AND keyword_distance < 0
    ),
    ranked_dense_hits AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            (ROW_NUMBER() OVER (
                ORDER BY menu.menu_vector <=> $3::vector(64), menu.menu_id, menu.cafe_id
            ))::integer AS dense_rank
        FROM cafe_menus AS menu
        JOIN candidate_cafes AS candidate
          ON candidate.cafe_id = menu.cafe_id
        WHERE menu.menu_vector IS NOT NULL
    ),
    dense_hits AS (
        SELECT
            cafe_id,
            menu_id,
            dense_rank
        FROM ranked_dense_hits
        WHERE dense_rank <= $5
    ),
    fused_hits AS (
        SELECT
            COALESCE(keyword_hits.cafe_id, dense_hits.cafe_id) AS cafe_id,
            COALESCE(keyword_hits.menu_id, dense_hits.menu_id) AS menu_id,
            keyword_hits.keyword_rank,
            dense_hits.dense_rank,
            calculate_rrf(
                keyword_hits.keyword_rank::integer,
                dense_hits.dense_rank::integer,
                $6::integer
            ) AS rrf_score
        FROM keyword_hits
        FULL OUTER JOIN dense_hits
            ON keyword_hits.cafe_id = dense_hits.cafe_id
           AND keyword_hits.menu_id = dense_hits.menu_id
    )
    SELECT
        fused_hits.cafe_id,
        fused_hits.menu_id,
        menu.menu_name,
        menu.menu_description,
        fused_hits.keyword_rank,
        fused_hits.dense_rank,
        fused_hits.rrf_score
    FROM fused_hits
    JOIN cafe_menus AS menu
      ON menu.cafe_id = fused_hits.cafe_id
     AND menu.menu_id = fused_hits.menu_id
    ORDER BY
        fused_hits.rrf_score DESC,
        COALESCE(fused_hits.keyword_rank, 2147483647),
        COALESCE(fused_hits.dense_rank, 2147483647),
        fused_hits.menu_id,
        fused_hits.cafe_id
"""

_CANDIDATE_MENU_SEARCH_KEYWORD_ONLY_QUERY = """
    WITH candidate_cafes AS (
        SELECT UNNEST($1::uuid[]) AS cafe_id
    ),
    scored_keyword_hits AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            menu.menu_search_text <@> to_bm25query($2, $3) AS keyword_distance
        FROM cafe_menus AS menu
        JOIN candidate_cafes AS candidate
          ON candidate.cafe_id = menu.cafe_id
        WHERE COALESCE(menu.menu_search_text, '') <> ''
    ),
    ranked_keyword_hits AS (
        SELECT
            cafe_id,
            menu_id,
            keyword_distance,
            (ROW_NUMBER() OVER (
                ORDER BY keyword_distance ASC, menu_id, cafe_id
            ))::integer AS keyword_rank
        FROM scored_keyword_hits
    )
    SELECT
        ranked_keyword_hits.cafe_id,
        ranked_keyword_hits.menu_id,
        menu.menu_name,
        menu.menu_description,
        ranked_keyword_hits.keyword_rank,
        NULL::integer AS dense_rank,
        calculate_rrf(
            ranked_keyword_hits.keyword_rank::integer,
            NULL::integer,
            $5::integer
        ) AS rrf_score
    FROM ranked_keyword_hits
    JOIN cafe_menus AS menu
      ON menu.cafe_id = ranked_keyword_hits.cafe_id
     AND menu.menu_id = ranked_keyword_hits.menu_id
    WHERE ranked_keyword_hits.keyword_rank <= $4
      AND ranked_keyword_hits.keyword_distance < 0
    ORDER BY
        rrf_score DESC,
        ranked_keyword_hits.keyword_rank,
        ranked_keyword_hits.menu_id,
        ranked_keyword_hits.cafe_id
"""


@dataclass(slots=True)
class CafeCandidate:
    cafe_id: UUID
    name: str
    address: str | None
    road_address: str | None
    cafe_intro: str | None
    brand_name: str | None
    branch_name: str | None


@dataclass(slots=True)
class MenuSearchHit:
    cafe_id: UUID
    menu_id: int
    menu_name: str
    menu_description: str | None
    keyword_rank: int | None
    dense_rank: int | None
    rrf_score: float


class MapSearchService:
    def __init__(
        self,
        query_preprocess_service: QueryPreprocessService | None = None,
    ) -> None:
        self._query_preprocess_service = query_preprocess_service or QueryPreprocessService()

    async def search(self, request: MapSearchRequest) -> MapSearchResponse:
        with track_map_search_stage("map_search_total"):
            logger.info(
                "map_search_started: user_id=%s keyword=%s mood_count=%s latitude=%.4f longitude=%.4f",
                request.user_id,
                request.keyword[:100],
                len(request.mood),
                request.latitude,
                request.longitude,
            )
            with track_map_search_stage("preprocess_total"):
                processed_query = await self._query_preprocess_service.preprocess(request.keyword)
            extracted_menus = list(processed_query.menu_phrases)
            logger.info(
                "map_search_menu_list_completed: menu_phrase_count=%s extracted_menus=%s",
                len(extracted_menus),
                extracted_menus[:_MENU_LOG_LIMIT],
            )
            if not extracted_menus:
                logger.info(
                    "map_search_no_menu_phrases: user_id=%s keyword=%s",
                    request.user_id,
                    request.keyword[:100],
                )
                return MapSearchResponse()

            with track_map_search_stage("candidate_lookup"):
                candidates = await self.get_candidates_within_radius(
                    latitude=request.latitude,
                    longitude=request.longitude,
                    mood_ids=request.mood,
                )
            logger.info(
                "map_search_candidates_filtered: candidate_count=%s cafe_names=%s",
                len(candidates),
                [candidate.name[:_MENU_NAME_LOG_LIMIT] for candidate in candidates[:20]],
            )
            if not candidates:
                logger.info(
                    "map_search_no_candidates: latitude=%.4f longitude=%.4f radius_meters=%s mood_count=%s",
                    request.latitude,
                    request.longitude,
                    _RADIUS_METERS,
                    len(request.mood),
                )
                return MapSearchResponse(extracted_menus=extracted_menus)

            sparse_query = self.build_sparse_query(extracted_menus)
            query_vector = await self._query_preprocess_service.encode_query(
                processed_query.normalized_query
            )
            logger.info(
                "map_search_query_encoding_completed: sparse_query=%s query_vector_dim=%s",
                sparse_query[:100],
                len(query_vector),
            )
            with track_map_search_stage("menu_lookup"):
                menu_hits = await self.search_menu_hits(
                    candidate_cafe_ids=[candidate.cafe_id for candidate in candidates],
                    sparse_query=sparse_query,
                    query_vector=query_vector,
                )
            if not menu_hits:
                logger.info(
                    "map_search_no_menu_hits: candidate_count=%s sparse_query=%s",
                    len(candidates),
                    sparse_query[:100],
                )
                return MapSearchResponse(extracted_menus=extracted_menus)

            ranked_cafe_ids = self.rank_cafes(menu_hits)
            cafes = {
                str(cafe_id): rank
                for rank, cafe_id in enumerate(ranked_cafe_ids[:_MAX_RESULTS], start=1)
            }
            logger.info(
                "map_search_ranking_completed: ranked_cafe_count=%s returned_cafe_count=%s top_cafe_ids=%s top_rrf_scores=%s",
                len(ranked_cafe_ids),
                len(cafes),
                [str(cafe_id) for cafe_id in ranked_cafe_ids[:_MENU_LOG_LIMIT]],
                self.summarize_top_cafe_scores(menu_hits, ranked_cafe_ids),
            )
            return MapSearchResponse(cafes=cafes, extracted_menus=extracted_menus)

    async def get_candidates_within_radius(
        self,
        *,
        latitude: float,
        longitude: float,
        mood_ids: list[UUID],
    ) -> list[CafeCandidate]:
        pool = get_pg_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                _RADIUS_MOOD_CAFE_QUERY,
                longitude,
                latitude,
                _RADIUS_METERS,
                mood_ids,
            )

        return [
            CafeCandidate(
                cafe_id=UUID(str(row["cafe_id"])),
                name=row["name"] or "",
                address=row["address"],
                road_address=row["road_address"],
                cafe_intro=row["cafe_intro"],
                brand_name=row["brand_name"],
                branch_name=row["branch_name"],
            )
            for row in rows
        ]

    async def search_menu_hits(
        self,
        *,
        candidate_cafe_ids: list[UUID],
        sparse_query: str,
        query_vector: list[float],
    ) -> list[MenuSearchHit]:
        normalized_sparse_query = sparse_query.strip()
        if not candidate_cafe_ids or not normalized_sparse_query:
            return []

        if query_vector:
            query = _CANDIDATE_MENU_SEARCH_FUSED_QUERY
            args: tuple[object, ...] = (
                candidate_cafe_ids,
                normalized_sparse_query,
                self.to_vector_literal(query_vector),
                _MENU_SEARCH_BM25_INDEX,
                _MENU_SEARCH_LIMIT,
                _RRF_K,
            )
            search_mode = "fused"
        else:
            query = _CANDIDATE_MENU_SEARCH_KEYWORD_ONLY_QUERY
            args = (
                candidate_cafe_ids,
                normalized_sparse_query,
                _MENU_SEARCH_BM25_INDEX,
                _MENU_SEARCH_LIMIT,
                _RRF_K,
            )
            search_mode = "keyword_only"

        logger.info(
            "map_search_menu_lookup_started: candidate_cafe_count=%s sparse_query=%s search_mode=%s query_vector_dim=%s",
            len(candidate_cafe_ids),
            normalized_sparse_query[:100],
            search_mode,
            len(query_vector),
        )
        pool = get_pg_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)

        hits = [
            MenuSearchHit(
                cafe_id=UUID(str(row["cafe_id"])),
                menu_id=int(row["menu_id"]),
                menu_name=row["menu_name"],
                menu_description=row["menu_description"],
                keyword_rank=int(row["keyword_rank"]) if row["keyword_rank"] is not None else None,
                dense_rank=int(row["dense_rank"]) if row["dense_rank"] is not None else None,
                rrf_score=float(row["rrf_score"]),
            )
            for row in rows
        ]
        logger.info(
            "map_search_menu_lookup_completed: search_mode=%s hit_count=%s top_hits=%s",
            search_mode,
            len(hits),
            self.summarize_menu_hits(hits),
        )
        if hits:
            top_hit = hits[0]
            logger.info(
                "map_search_menu_rrf_completed: top_menu_name=%s top_menu_id=%s keyword_rank=%s dense_rank=%s rrf_score=%.6f",
                top_hit.menu_name[:_MENU_NAME_LOG_LIMIT],
                top_hit.menu_id,
                top_hit.keyword_rank,
                top_hit.dense_rank,
                top_hit.rrf_score,
            )
        return hits

    def build_sparse_query(self, menu_phrases: list[str]) -> str:
        deduplicated_phrases: list[str] = []
        seen_phrases: set[str] = set()
        for phrase in menu_phrases:
            normalized_phrase = self.normalize_text(phrase)
            if not normalized_phrase or normalized_phrase in seen_phrases:
                continue
            seen_phrases.add(normalized_phrase)
            deduplicated_phrases.append(normalized_phrase)
        return " ".join(deduplicated_phrases)

    def rank_cafes(self, menu_hits: list[MenuSearchHit]) -> list[UUID]:
        best_hit_by_cafe: dict[UUID, MenuSearchHit] = {}
        for hit in menu_hits:
            best_hit = best_hit_by_cafe.get(hit.cafe_id)
            if best_hit is None or self.menu_hit_sort_key(hit) < self.menu_hit_sort_key(best_hit):
                best_hit_by_cafe[hit.cafe_id] = hit

        ordered_cafes = sorted(
            best_hit_by_cafe.items(),
            key=lambda item: (
                -item[1].rrf_score,
                self.rank_value(item[1].keyword_rank),
                self.rank_value(item[1].dense_rank),
                str(item[0]),
            ),
        )
        return [cafe_id for cafe_id, _ in ordered_cafes]

    def summarize_menu_hits(self, hits: list[MenuSearchHit]) -> list[dict[str, object]]:
        return [
            {
                "menu_id": hit.menu_id,
                "cafe_id": str(hit.cafe_id),
                "menu_name": hit.menu_name[:_MENU_NAME_LOG_LIMIT],
                "keyword_rank": hit.keyword_rank,
                "dense_rank": hit.dense_rank,
                "rrf_score": round(hit.rrf_score, 6),
            }
            for hit in hits[:_MENU_LOG_LIMIT]
        ]

    def summarize_top_cafe_scores(
        self,
        menu_hits: list[MenuSearchHit],
        ranked_cafe_ids: list[UUID],
    ) -> list[float]:
        best_hit_by_cafe: dict[UUID, MenuSearchHit] = {}
        for hit in menu_hits:
            best_hit = best_hit_by_cafe.get(hit.cafe_id)
            if best_hit is None or self.menu_hit_sort_key(hit) < self.menu_hit_sort_key(best_hit):
                best_hit_by_cafe[hit.cafe_id] = hit
        return [
            round(best_hit_by_cafe[cafe_id].rrf_score, 6)
            for cafe_id in ranked_cafe_ids[:_MENU_LOG_LIMIT]
            if cafe_id in best_hit_by_cafe
        ]

    def menu_hit_sort_key(self, hit: MenuSearchHit) -> tuple[float, int, int, int, str]:
        return (
            -hit.rrf_score,
            self.rank_value(hit.keyword_rank),
            self.rank_value(hit.dense_rank),
            hit.menu_id,
            str(hit.cafe_id),
        )

    def rank_value(self, value: int | None) -> int:
        return value if value is not None else _DEFAULT_RANK

    def normalize_text(self, value: str) -> str:
        return " ".join(value.strip().split()).casefold()

    def to_vector_literal(self, vector: list[float]) -> str:
        return to_shared_vector_literal(vector)
