from __future__ import annotations

import asyncpg
from collections import Counter, defaultdict
from dataclasses import dataclass
import logging
import re
from uuid import UUID

from app.core.config import settings
from app.db.postgresql import get_pg_pool
from app.models.map_search import MapSearchRequest, MapSearchResponse
from app.services.preference_vector import USER_PREFERENCE_QUERY as _SHARED_USER_PREFERENCE_QUERY
from app.services.preference_vector import (
    UserPreferenceNotFoundError,
    fetch_user_preference_vector,
    parse_vector_literal as parse_shared_vector_literal,
    to_vector_literal as to_shared_vector_literal,
)
from app.services.query_preprocess_service import QueryPreprocessService

logger = logging.getLogger("uvicorn.error")

_RADIUS_METERS = 2000
_MAX_RESULTS = settings.discovery_top_k
_MENU_SEARCH_LIMIT = 20
_MENU_LOG_LIMIT = 5
_MENU_SEARCH_BM25_INDEX = "cafe_menus_menu_search_bm25_idx"
_RRF_K = 60
_MENU_NAME_LOG_LIMIT = 80
_LEGACY_MENU_SEARCH_TEXT_SQL = "concat_ws(' ', menu.menu_name, COALESCE(menu.menu_description, ''))"
_MOOD_KEYWORDS: dict[str, tuple[str, ...]] = {
    "7ab663df-31be-43f8-b06a-2e8979806d89": (
        "우드톤",
        "따뜻함",
        "따뜻한",
        "아늑한",
        "포근한",
    ),
    "4ada6e46-3d5b-4ac8-abf9-9479abb35cfc": (
        "식물원",
        "플랜테리어",
        "식물",
        "초록",
        "녹음",
    ),
    "c35facb1-f2ae-42aa-8234-522f6ae3352b": (
        "힙한",
        "힙",
        "트렌디",
        "감성",
        "감각적인",
    ),
    "e747e844-db71-42ea-81cf-c25d510672b2": (
        "조용한",
        "조용",
        "차분한",
        "차분",
        "고요한",
    ),
    "9b71769c-2293-4e06-bf37-f1fbf33c2853": (
        "탁트인",
        "탁 트인",
        "뷰 좋은",
        "뷰",
        "전망",
        "창가",
    ),
}

_USER_PREFERENCE_QUERY = _SHARED_USER_PREFERENCE_QUERY

_RADIUS_CAFE_QUERY = """
    SELECT
        cafe_id,
        name,
        address,
        road_address,
        cafe_intro,
        brand_name,
        branch_name,
        1 - (cafe_vector <=> $1::vector) AS preference_similarity
    FROM cafes
    WHERE cafe_vector IS NOT NULL
      AND ST_DWithin(
          location,
          ST_SetSRID(ST_MakePoint($2, $3), 4326)::geography,
          $4
      )
"""

_RADIUS_MENU_CAFE_QUERY = """
    WITH phrase_list AS (
        SELECT DISTINCT LOWER(REGEXP_REPLACE(BTRIM(phrase), '\\s+', ' ', 'g')) AS normalized_phrase
        FROM UNNEST($5::text[]) AS phrase
        WHERE COALESCE(BTRIM(phrase), '') <> ''
    )
    SELECT
        cafe.cafe_id,
        cafe.name,
        cafe.address,
        cafe.road_address,
        cafe.cafe_intro,
        cafe.brand_name,
        cafe.branch_name,
        COUNT(DISTINCT phrase_list.normalized_phrase) AS matched_phrase_count,
        1 - (cafe.cafe_vector <=> $1::vector) AS preference_similarity
    FROM cafes AS cafe
    JOIN cafe_menus AS menu
      ON menu.cafe_id = cafe.cafe_id
    JOIN phrase_list
      ON LOWER(REGEXP_REPLACE(menu.menu_name, '\\s+', ' ', 'g')) LIKE '%' || phrase_list.normalized_phrase || '%'
    WHERE cafe.cafe_vector IS NOT NULL
      AND ST_DWithin(
          cafe.location,
          ST_SetSRID(ST_MakePoint($2, $3), 4326)::geography,
          $4
      )
    GROUP BY
        cafe.cafe_id,
        cafe.name,
        cafe.address,
        cafe.road_address,
        cafe.cafe_intro,
        cafe.brand_name,
        cafe.branch_name,
        cafe.cafe_vector
"""

_CAFE_MENU_QUERY = """
    SELECT
        cafe_id,
        menu_id,
        menu_name,
        menu_description
    FROM cafe_menus
    WHERE cafe_id = ANY($1::uuid[])
    ORDER BY cafe_id, menu_id
"""

_CAFE_MENU_QUERY_LEGACY = f"""
    SELECT
        cafe_id,
        menu_id,
        menu_name,
        menu_description,
        {_LEGACY_MENU_SEARCH_TEXT_SQL} AS menu_search_text
    FROM cafe_menus AS menu
    WHERE cafe_id = ANY($1::uuid[])
    ORDER BY cafe_id, menu_id
"""

_CAFE_MENU_SEARCH_KEYWORD_ONLY_QUERY = f"""
    WITH scored_keyword_hits AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            menu.menu_name,
            menu.menu_description,
            menu.menu_search_text <@> to_bm25query($2, $3) AS keyword_distance
        FROM cafe_menus AS menu
        WHERE menu.cafe_id = ANY($1::uuid[])
          AND COALESCE(menu.menu_search_text, '') <> ''
    ),
    ranked_keyword_hits AS (
        SELECT
            cafe_id,
            menu_id,
            menu_name,
            menu_description,
            keyword_distance,
            ROW_NUMBER() OVER (
                ORDER BY keyword_distance ASC, menu_id
            ) AS keyword_rank
        FROM scored_keyword_hits
    )
    SELECT
        cafe_id,
        menu_id,
        menu_name,
        menu_description,
        keyword_rank,
        NULL::integer AS vector_rank,
        1.0 / ({_RRF_K} + keyword_rank) AS rrf_score
    FROM ranked_keyword_hits
    WHERE keyword_rank <= $4
      AND keyword_distance < 0
    ORDER BY rrf_score DESC, keyword_rank, menu_id
"""

_CAFE_MENU_SEARCH_KEYWORD_ONLY_GLOBAL_QUERY = f"""
    WITH scored_keyword_hits AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            menu.menu_name,
            menu.menu_description,
            menu.menu_search_text <@> to_bm25query($1, $2) AS keyword_distance
        FROM cafe_menus AS menu
        WHERE COALESCE(menu.menu_search_text, '') <> ''
    ),
    ranked_keyword_hits AS (
        SELECT
            cafe_id,
            menu_id,
            menu_name,
            menu_description,
            keyword_distance,
            ROW_NUMBER() OVER (
                ORDER BY keyword_distance ASC, menu_id
            ) AS keyword_rank
        FROM scored_keyword_hits
    )
    SELECT
        cafe_id,
        menu_id,
        menu_name,
        menu_description,
        keyword_rank,
        NULL::integer AS vector_rank,
        1.0 / ({_RRF_K} + keyword_rank) AS rrf_score
    FROM ranked_keyword_hits
    WHERE keyword_rank <= $3
      AND keyword_distance < 0
    ORDER BY rrf_score DESC, keyword_rank, menu_id
"""

_CAFE_MENU_SEARCH_LEGACY_QUERY = f"""
    WITH menu_source AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            menu.menu_name,
            menu.menu_description,
            {_LEGACY_MENU_SEARCH_TEXT_SQL} AS searchable_text
        FROM cafe_menus AS menu
        WHERE menu.cafe_id = ANY($1::uuid[])
    ),
    matched_hits AS (
        SELECT
            cafe_id,
            menu_id,
            menu_name,
            menu_description,
            CASE
                WHEN LOWER(menu_name) = LOWER($2) THEN 0
                WHEN LOWER(menu_name) LIKE LOWER($2) || '%' THEN 1
                ELSE 2
            END AS match_rank,
            POSITION(LOWER($2) IN LOWER(searchable_text)) AS match_position
        FROM menu_source
        WHERE LOWER(searchable_text) LIKE '%' || LOWER($2) || '%'
    ),
    ranked_hits AS (
        SELECT
            cafe_id,
            menu_id,
            menu_name,
            menu_description,
            ROW_NUMBER() OVER (
                ORDER BY match_rank ASC, match_position ASC, menu_id
            ) AS keyword_rank
        FROM matched_hits
    )
    SELECT
        cafe_id,
        menu_id,
        menu_name,
        menu_description,
        keyword_rank,
        NULL::integer AS vector_rank,
        1.0 / ({_RRF_K} + keyword_rank) AS rrf_score
    FROM ranked_hits
    WHERE keyword_rank <= $3
    ORDER BY rrf_score DESC, keyword_rank, menu_id
"""

_CAFE_MENU_SEARCH_LEGACY_GLOBAL_QUERY = f"""
    WITH menu_source AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            menu.menu_name,
            menu.menu_description,
            {_LEGACY_MENU_SEARCH_TEXT_SQL} AS searchable_text
        FROM cafe_menus AS menu
    ),
    matched_hits AS (
        SELECT
            cafe_id,
            menu_id,
            menu_name,
            menu_description,
            CASE
                WHEN LOWER(menu_name) = LOWER($1) THEN 0
                WHEN LOWER(menu_name) LIKE LOWER($1) || '%' THEN 1
                ELSE 2
            END AS match_rank,
            POSITION(LOWER($1) IN LOWER(searchable_text)) AS match_position
        FROM menu_source
        WHERE LOWER(searchable_text) LIKE '%' || LOWER($1) || '%'
    ),
    ranked_hits AS (
        SELECT
            cafe_id,
            menu_id,
            menu_name,
            menu_description,
            ROW_NUMBER() OVER (
                ORDER BY match_rank ASC, match_position ASC, menu_id
            ) AS keyword_rank
        FROM matched_hits
    )
    SELECT
        cafe_id,
        menu_id,
        menu_name,
        menu_description,
        keyword_rank,
        NULL::integer AS vector_rank,
        1.0 / ({_RRF_K} + keyword_rank) AS rrf_score
    FROM ranked_hits
    WHERE keyword_rank <= $2
    ORDER BY rrf_score DESC, keyword_rank, menu_id
"""

_CAFE_MENU_SEARCH_FUSED_QUERY = """
    WITH scored_keyword_hits AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            menu.menu_search_text <@> to_bm25query($2, $4) AS keyword_distance
        FROM cafe_menus AS menu
        WHERE menu.cafe_id = ANY($1::uuid[])
          AND COALESCE(menu.menu_search_text, '') <> ''
    ),
    ranked_keyword_hits AS (
        SELECT
            cafe_id,
            menu_id,
            keyword_distance,
            ROW_NUMBER() OVER (
                ORDER BY keyword_distance ASC, menu_id
            ) AS keyword_rank
        FROM scored_keyword_hits
    ),
    keyword_hits AS (
        SELECT cafe_id, menu_id, keyword_rank
        FROM ranked_keyword_hits
        WHERE keyword_rank <= $5
          AND keyword_distance < 0
    ),
    ranked_vector_hits AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            ROW_NUMBER() OVER (
                ORDER BY menu.menu_vector <=> $3::vector(64), menu.menu_id
            ) AS vector_rank
        FROM cafe_menus AS menu
        WHERE menu.cafe_id = ANY($1::uuid[])
          AND menu.menu_vector IS NOT NULL
    ),
    vector_hits AS (
        SELECT cafe_id, menu_id, vector_rank
        FROM ranked_vector_hits
        WHERE vector_rank <= $5
    ),
    fused_hits AS (
        SELECT
            COALESCE(keyword_hits.cafe_id, vector_hits.cafe_id) AS cafe_id,
            COALESCE(keyword_hits.menu_id, vector_hits.menu_id) AS menu_id,
            keyword_hits.keyword_rank,
            vector_hits.vector_rank,
            calculate_rrf(keyword_hits.keyword_rank, vector_hits.vector_rank) AS rrf_score
        FROM keyword_hits
        FULL OUTER JOIN vector_hits
            ON keyword_hits.cafe_id = vector_hits.cafe_id
           AND keyword_hits.menu_id = vector_hits.menu_id
    )
    SELECT
        fused_hits.cafe_id,
        fused_hits.menu_id,
        menu.menu_name,
        menu.menu_description,
        fused_hits.keyword_rank,
        fused_hits.vector_rank,
        fused_hits.rrf_score
    FROM fused_hits
    JOIN cafe_menus AS menu
      ON menu.cafe_id = fused_hits.cafe_id
     AND menu.menu_id = fused_hits.menu_id
    ORDER BY
        fused_hits.rrf_score DESC,
        COALESCE(fused_hits.keyword_rank, 2147483647),
        COALESCE(fused_hits.vector_rank, 2147483647),
        fused_hits.menu_id
"""

_CAFE_MENU_SEARCH_FUSED_GLOBAL_QUERY = """
    WITH scored_keyword_hits AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            menu.menu_search_text <@> to_bm25query($1, $3) AS keyword_distance
        FROM cafe_menus AS menu
        WHERE COALESCE(menu.menu_search_text, '') <> ''
    ),
    ranked_keyword_hits AS (
        SELECT
            cafe_id,
            menu_id,
            keyword_distance,
            ROW_NUMBER() OVER (
                ORDER BY keyword_distance ASC, menu_id
            ) AS keyword_rank
        FROM scored_keyword_hits
    ),
    keyword_hits AS (
        SELECT cafe_id, menu_id, keyword_rank
        FROM ranked_keyword_hits
        WHERE keyword_rank <= $4
          AND keyword_distance < 0
    ),
    ranked_vector_hits AS (
        SELECT
            menu.cafe_id,
            menu.menu_id,
            ROW_NUMBER() OVER (
                ORDER BY menu.menu_vector <=> $2::vector(64), menu.menu_id
            ) AS vector_rank
        FROM cafe_menus AS menu
        WHERE menu.menu_vector IS NOT NULL
    ),
    vector_hits AS (
        SELECT cafe_id, menu_id, vector_rank
        FROM ranked_vector_hits
        WHERE vector_rank <= $4
    ),
    fused_hits AS (
        SELECT
            COALESCE(keyword_hits.cafe_id, vector_hits.cafe_id) AS cafe_id,
            COALESCE(keyword_hits.menu_id, vector_hits.menu_id) AS menu_id,
            keyword_hits.keyword_rank,
            vector_hits.vector_rank,
            calculate_rrf(keyword_hits.keyword_rank, vector_hits.vector_rank) AS rrf_score
        FROM keyword_hits
        FULL OUTER JOIN vector_hits
            ON keyword_hits.cafe_id = vector_hits.cafe_id
           AND keyword_hits.menu_id = vector_hits.menu_id
    )
    SELECT
        fused_hits.cafe_id,
        fused_hits.menu_id,
        menu.menu_name,
        menu.menu_description,
        fused_hits.keyword_rank,
        fused_hits.vector_rank,
        fused_hits.rrf_score
    FROM fused_hits
    JOIN cafe_menus AS menu
      ON menu.cafe_id = fused_hits.cafe_id
     AND menu.menu_id = fused_hits.menu_id
    ORDER BY
        fused_hits.rrf_score DESC,
        COALESCE(fused_hits.keyword_rank, 2147483647),
        COALESCE(fused_hits.vector_rank, 2147483647),
        fused_hits.menu_id
"""


@dataclass(slots=True)
class CafeCandidate:
    cafe_id: UUID
    preference_similarity: float
    matched_phrase_count: int
    name: str
    address: str | None
    road_address: str | None
    cafe_intro: str | None
    brand_name: str | None
    branch_name: str | None


@dataclass(slots=True)
class CafeMenu:
    cafe_id: UUID
    menu_id: int
    menu_name: str
    menu_description: str | None
    menu_search_text: str | None = None


@dataclass(slots=True)
class MenuSearchHit:
    phrase: str
    cafe_id: UUID
    menu_id: int
    menu_name: str
    menu_description: str | None
    keyword_rank: int | None
    vector_rank: int | None
    rrf_score: float


@dataclass(slots=True)
class ResolvedMenuNameMatch:
    phrase: str
    normalized_phrase: str
    menu_name: str
    normalized_menu_name: str
    top_hit: MenuSearchHit
    grouped_hits: list[MenuSearchHit]


class MapSearchService:
    def __init__(
        self,
        query_preprocess_service: QueryPreprocessService | None = None,
    ) -> None:
        self._query_preprocess_service = query_preprocess_service or QueryPreprocessService()

    async def search(self, request: MapSearchRequest) -> MapSearchResponse:
        logger.info(
            "map_search_started: user_id=%s keyword=%s mood_count=%s latitude=%.4f longitude=%.4f",
            request.user_id,
            request.keyword[:100],
            len(request.mood),
            request.latitude,
            request.longitude,
        )
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

        mood_keywords = self.resolve_mood_keywords(request.mood)
        user_preference_vector = await self.get_user_preference_vector(request.user_id)

        candidates = await self.get_candidates_within_radius(
            latitude=request.latitude,
            longitude=request.longitude,
            preference_vector=user_preference_vector,
            menu_phrases=extracted_menus,
        )
        candidate_ids = [candidate.cafe_id for candidate in candidates]
        menus_by_cafe = await self.get_cafe_menus(candidate_ids)
        logger.info(
            "map_search_candidates_loaded: candidate_count=%s matched_phrase_count=%s cafe_count_with_menus=%s menu_row_count=%s",
            len(candidates),
            max((candidate.matched_phrase_count for candidate in candidates), default=0),
            len(menus_by_cafe),
            sum(len(menus) for menus in menus_by_cafe.values()),
        )
        if not candidates:
            logger.info(
                "map_search_no_candidates: latitude=%.4f longitude=%.4f radius_meters=%s extracted_menus=%s",
                request.latitude,
                request.longitude,
                _RADIUS_METERS,
                extracted_menus[:_MENU_LOG_LIMIT],
            )
            return MapSearchResponse(extracted_menus=extracted_menus)

        ranked_cafe_ids = self.rank_cafes(
            candidates=candidates,
            menus_by_cafe=menus_by_cafe,
            mood_keywords=mood_keywords,
        )
        if not ranked_cafe_ids:
            return MapSearchResponse(extracted_menus=extracted_menus)

        cafes = {
            str(cafe_id): rank
            for rank, cafe_id in enumerate(ranked_cafe_ids[:_MAX_RESULTS], start=1)
        }
        logger.info(
            "map_search_ranking_completed: ranked_cafe_count=%s returned_cafe_count=%s top_cafe_ids=%s top_vector_similarity=%s",
            len(ranked_cafe_ids),
            len(cafes),
            [str(cafe_id) for cafe_id in ranked_cafe_ids[:_MENU_LOG_LIMIT]],
            [
                round(candidate.preference_similarity, 6)
                for candidate in candidates
                if candidate.cafe_id in ranked_cafe_ids[:_MENU_LOG_LIMIT]
            ],
        )
        return MapSearchResponse(cafes=cafes, extracted_menus=extracted_menus)

    async def get_user_preference_vector(self, user_id: UUID) -> list[float]:
        pool = get_pg_pool()

        async with pool.acquire() as conn:
            return await fetch_user_preference_vector(conn, user_id)

    async def get_candidates_within_radius(
        self,
        *,
        latitude: float,
        longitude: float,
        preference_vector: list[float],
        menu_phrases: list[str],
    ) -> list[CafeCandidate]:
        if not menu_phrases:
            return []

        pool = get_pg_pool()
        vector_literal = self.to_vector_literal(preference_vector)

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                _RADIUS_MENU_CAFE_QUERY,
                vector_literal,
                longitude,
                latitude,
                _RADIUS_METERS,
                menu_phrases,
            )

        return [
            CafeCandidate(
                cafe_id=UUID(str(row["cafe_id"])),
                preference_similarity=self.clamp_similarity(row["preference_similarity"]),
                matched_phrase_count=int(row["matched_phrase_count"] or 0),
                name=row["name"] or "",
                address=row["address"],
                road_address=row["road_address"],
                cafe_intro=row["cafe_intro"],
                brand_name=row["brand_name"],
                branch_name=row["branch_name"],
            )
            for row in rows
        ]

    async def get_cafe_menus(self, cafe_ids: list[UUID]) -> dict[UUID, list[CafeMenu]]:
        if not cafe_ids:
            return {}

        pool = get_pg_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(_CAFE_MENU_QUERY, cafe_ids)

        menus_by_cafe: dict[UUID, list[CafeMenu]] = defaultdict(list)
        for row in rows:
            cafe_id = UUID(str(row["cafe_id"]))
            menus_by_cafe[cafe_id].append(
                CafeMenu(
                    cafe_id=cafe_id,
                    menu_id=int(row["menu_id"]),
                    menu_name=row["menu_name"],
                    menu_description=row["menu_description"],
                )
            )

        return dict(menus_by_cafe)

    async def search_menu_hits(
        self,
        *,
        candidate_cafe_ids: list[UUID],
        phrase: str,
        phrase_vector: list[float],
    ) -> list[MenuSearchHit]:
        normalized_phrase = phrase.strip()
        if not normalized_phrase:
            return []

        pool = get_pg_pool()
        search_scope = "candidate" if candidate_cafe_ids else "global"
        search_mode = "fused" if phrase_vector else "keyword_only"
        logger.info(
            "map_search_menu_lookup_started: phrase=%s candidate_cafe_count=%s search_scope=%s search_mode=%s phrase_vector_dim=%s",
            normalized_phrase[:100],
            len(candidate_cafe_ids),
            search_scope,
            search_mode,
            len(phrase_vector),
        )
        if phrase_vector:
            if candidate_cafe_ids:
                query = _CAFE_MENU_SEARCH_FUSED_QUERY
                args: tuple[object, ...] = (
                    candidate_cafe_ids,
                    normalized_phrase,
                    self.to_vector_literal(phrase_vector),
                    _MENU_SEARCH_BM25_INDEX,
                    _MENU_SEARCH_LIMIT,
                )
            else:
                query = _CAFE_MENU_SEARCH_FUSED_GLOBAL_QUERY
                args = (
                    normalized_phrase,
                    self.to_vector_literal(phrase_vector),
                    _MENU_SEARCH_BM25_INDEX,
                    _MENU_SEARCH_LIMIT,
                )
        else:
            if candidate_cafe_ids:
                query = _CAFE_MENU_SEARCH_KEYWORD_ONLY_QUERY
                args = (
                    candidate_cafe_ids,
                    normalized_phrase,
                    _MENU_SEARCH_BM25_INDEX,
                    _MENU_SEARCH_LIMIT,
                )
            else:
                query = _CAFE_MENU_SEARCH_KEYWORD_ONLY_GLOBAL_QUERY
                args = (
                    normalized_phrase,
                    _MENU_SEARCH_BM25_INDEX,
                    _MENU_SEARCH_LIMIT,
                )

        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *args)

        hits = [
            MenuSearchHit(
                phrase=normalized_phrase,
                cafe_id=UUID(str(row["cafe_id"])),
                menu_id=int(row["menu_id"]),
                menu_name=row["menu_name"],
                menu_description=row["menu_description"],
                keyword_rank=int(row["keyword_rank"]) if row["keyword_rank"] is not None else None,
                vector_rank=int(row["vector_rank"]) if row["vector_rank"] is not None else None,
                rrf_score=float(row["rrf_score"]),
            )
            for row in rows
        ]
        keyword_hits = [hit for hit in hits if hit.keyword_rank is not None]
        vector_hits = [hit for hit in hits if hit.vector_rank is not None]
        logger.info(
            "map_search_menu_lookup_completed: phrase=%s search_scope=%s search_mode=%s hit_count=%s top_hits=%s",
            normalized_phrase[:100],
            search_scope,
            search_mode,
            len(hits),
            self.summarize_menu_hits(hits),
        )
        logger.info(
            "map_search_menu_keyword_hits: phrase=%s hit_count=%s top_menu_ids=%s",
            normalized_phrase[:100],
            len(keyword_hits),
            [hit.menu_id for hit in keyword_hits[:_MENU_LOG_LIMIT]],
        )
        logger.info(
            "map_search_menu_vector_hits: phrase=%s hit_count=%s top_menu_ids=%s",
            normalized_phrase[:100],
            len(vector_hits),
            [hit.menu_id for hit in vector_hits[:_MENU_LOG_LIMIT]],
        )
        if hits:
            top_hit = hits[0]
            logger.info(
                "map_search_menu_rrf_completed: phrase=%s top_menu_name=%s top_menu_id=%s bm25_rank=%s vector_rank=%s rrf_score=%.6f",
                normalized_phrase[:100],
                top_hit.menu_name[:_MENU_NAME_LOG_LIMIT],
                top_hit.menu_id,
                top_hit.keyword_rank,
                top_hit.vector_rank,
                top_hit.rrf_score,
            )
        else:
            logger.info(
                "map_search_menu_rrf_completed: phrase=%s top_menu_name=%s top_menu_id=%s bm25_rank=%s vector_rank=%s rrf_score=%.6f",
                normalized_phrase[:100],
                None,
                None,
                None,
                None,
                0.0,
            )
        return hits

    def resolve_menu_name_match(
        self,
        *,
        phrase: str,
        hits: list[MenuSearchHit],
    ) -> ResolvedMenuNameMatch | None:
        grouped_hits: dict[str, list[MenuSearchHit]] = defaultdict(list)
        for hit in hits:
            normalized_menu_name = self.normalize_menu_name(hit.menu_name)
            if not normalized_menu_name:
                continue
            grouped_hits[normalized_menu_name].append(hit)

        resolved_matches: list[ResolvedMenuNameMatch] = []
        for normalized_menu_name, menu_name_hits in grouped_hits.items():
            ordered_hits = sorted(menu_name_hits, key=self.menu_hit_sort_key)
            top_hit = ordered_hits[0]
            resolved_matches.append(
                ResolvedMenuNameMatch(
                    phrase=phrase.strip(),
                    normalized_phrase=self.normalize_menu_name(phrase),
                    menu_name=top_hit.menu_name.strip(),
                    normalized_menu_name=normalized_menu_name,
                    top_hit=top_hit,
                    grouped_hits=ordered_hits,
                )
            )

        if not resolved_matches:
            return None

        return sorted(resolved_matches, key=lambda item: self.menu_hit_sort_key(item.top_hit))[0]

    def build_extracted_menu_names(
        self,
        *,
        menu_phrases: list[str],
        resolved_menu_matches: dict[str, ResolvedMenuNameMatch],
    ) -> list[str]:
        extracted_menu_names: list[str] = []
        for phrase in menu_phrases:
            normalized_phrase = self.normalize_menu_name(phrase)
            if not normalized_phrase:
                continue
            resolved_match = resolved_menu_matches.get(normalized_phrase)
            if resolved_match is None:
                continue
            extracted_menu_names.append(resolved_match.menu_name)
        return extracted_menu_names

    def summarize_menu_hits(self, hits: list[MenuSearchHit]) -> list[dict[str, object]]:
        summaries: list[dict[str, object]] = []
        for hit in hits[:_MENU_LOG_LIMIT]:
            summaries.append(
                {
                    "menu_id": hit.menu_id,
                    "cafe_id": str(hit.cafe_id),
                    "menu_name": hit.menu_name[:_MENU_NAME_LOG_LIMIT],
                    "keyword_rank": hit.keyword_rank,
                    "vector_rank": hit.vector_rank,
                    "rrf_score": round(hit.rrf_score, 6),
                }
            )
        return summaries

    def menu_hit_sort_key(self, hit: MenuSearchHit) -> tuple[float, int, int, int, str]:
        return (
            -hit.rrf_score,
            hit.keyword_rank if hit.keyword_rank is not None else 2147483647,
            hit.vector_rank if hit.vector_rank is not None else 2147483647,
            hit.menu_id,
            str(hit.cafe_id),
        )

    def rank_cafes(
        self,
        *,
        candidates: list[CafeCandidate],
        menus_by_cafe: dict[UUID, list[CafeMenu]],
        mood_keywords: list[str],
    ) -> list[UUID]:
        mood_terms = self.build_keyword_terms(" ".join(mood_keywords))
        scored_candidates: list[tuple[float, float, str, UUID]] = []

        for candidate in candidates:
            searchable_text = self.build_searchable_text(
                candidate,
                menus_by_cafe.get(candidate.cafe_id, []),
            )
            mood_score = self.score_text_terms(mood_terms, searchable_text)
            scored_candidates.append(
                (
                    candidate.preference_similarity,
                    mood_score,
                    str(candidate.cafe_id),
                    candidate.cafe_id,
                )
            )

        scored_candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
        return [item[3] for item in scored_candidates]

    def collect_menu_phrase_counts(
        self,
        *,
        normalized_query: str,
        menu_phrases: list[str],
    ) -> Counter[str]:
        phrase_counts: Counter[str] = Counter()
        for phrase in menu_phrases:
            normalized_phrase = phrase.strip()
            if not normalized_phrase:
                continue
            extracted_count = sum(1 for item in menu_phrases if item.strip() == normalized_phrase)
            query_count = normalized_query.casefold().count(normalized_phrase.casefold())
            phrase_counts[normalized_phrase] = max(1, extracted_count, query_count)
        return phrase_counts

    def normalize_menu_name(self, menu_name: str) -> str:
        return re.sub(r"\s+", " ", menu_name).strip().casefold()

    def build_residual_keyword(self, normalized_query: str, resolved_phrases: list[str]) -> str:
        residual = normalized_query
        for phrase in sorted({value.strip() for value in resolved_phrases if value.strip()}, key=len, reverse=True):
            residual = re.sub(re.escape(phrase), " ", residual, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", residual).strip()

    def resolve_mood_keywords(self, mood: list[UUID]) -> list[str]:
        resolved_keywords: list[str] = []
        seen_keywords: set[str] = set()

        for mood_id in mood:
            for keyword in _MOOD_KEYWORDS.get(str(mood_id), ()):
                normalized_keyword = keyword.strip()
                if not normalized_keyword or normalized_keyword in seen_keywords:
                    continue
                seen_keywords.add(normalized_keyword)
                resolved_keywords.append(normalized_keyword)

        return resolved_keywords

    def build_keyword_terms(self, text: str) -> list[str]:
        keyword_terms: list[str] = []
        normalized_text = text.strip()

        if normalized_text:
            keyword_terms.append(normalized_text.casefold())
            keyword_terms.extend(self.tokenize(normalized_text))

        deduplicated_terms: list[str] = []
        seen_terms: set[str] = set()
        for term in keyword_terms:
            normalized_term = term.strip()
            if not normalized_term or normalized_term in seen_terms:
                continue
            seen_terms.add(normalized_term)
            deduplicated_terms.append(normalized_term)
        return deduplicated_terms

    def build_searchable_text(
        self,
        candidate: CafeCandidate,
        menus: list[CafeMenu],
    ) -> str:
        text_parts = [
            candidate.name,
            candidate.brand_name or "",
            candidate.branch_name or "",
            candidate.address or "",
            candidate.road_address or "",
            candidate.cafe_intro or "",
        ]
        for menu in menus:
            text_parts.append(menu.menu_name)
        return " ".join(part for part in text_parts if part).casefold()

    def score_text_terms(self, terms: list[str], searchable_text: str) -> float:
        if not terms or not searchable_text:
            return 0.0

        return float(sum(searchable_text.count(term) for term in terms))

    def tokenize(self, text: str) -> list[str]:
        return [
            token.casefold()
            for token in re.split(r"[\s/|,+]+", text)
            if token.strip()
        ]

    def clamp_similarity(self, value: object) -> float:
        if value is None:
            return 0.0
        numeric_value = float(value)
        return max(-1.0, min(numeric_value, 1.0))

    def to_vector_literal(self, vector: list[float]) -> str:
        return to_shared_vector_literal(vector)

    def parse_vector_literal(self, vector_literal: str) -> list[float]:
        return parse_shared_vector_literal(vector_literal)
