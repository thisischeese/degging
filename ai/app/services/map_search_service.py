from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.db.postgresql import get_pg_pool
from app.models.map_search import MapSearchRequest, MapSearchResponse
from app.services.discovery_service import DiscoveryService
from app.services.query_preprocess_service import QueryPreprocessService

_RADIUS_METERS = 2000
_MAX_RESULTS = settings.discovery_top_k

_RADIUS_CAFE_QUERY = """
    SELECT
        cafes.cafe_id,
        1 - (cafe_embeddings.embedding <=> $1::vector) AS preference_similarity
    FROM cafes
    JOIN cafe_embeddings
        ON cafe_embeddings.cafe_id = cafes.cafe_id
    WHERE ST_DWithin(
        cafes.location,
        ST_SetSRID(ST_MakePoint($2, $3), 4326)::geography,
        $4
    )
"""

_QUERY_SIMILARITY_QUERY = """
    SELECT
        cafe_id,
        1 - (embedding <=> $1::vector) AS query_similarity
    FROM cafe_embeddings
    WHERE cafe_id = ANY($2::uuid[])
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


@dataclass(slots=True)
class CafeCandidate:
    cafe_id: UUID
    preference_similarity: float


@dataclass(slots=True)
class CafeMenu:
    cafe_id: UUID
    menu_id: int
    menu_name: str
    menu_description: str | None


class MapSearchService:
    def __init__(
        self,
        mongo_db: AsyncIOMotorDatabase,
        query_preprocess_service: QueryPreprocessService | None = None,
        discovery_service: DiscoveryService | None = None,
    ) -> None:
        self._query_preprocess_service = query_preprocess_service or QueryPreprocessService()
        self._discovery_service = discovery_service or DiscoveryService(mongo_db)

    async def search(self, request: MapSearchRequest) -> MapSearchResponse:
        processed_query = await self._query_preprocess_service.preprocess(request.keyword)
        mood_keywords = self.resolve_mood_keywords(request.mood)
        user_preference_vector = await self._discovery_service.get_user_preference_vector(
            request.user_id
        )

        candidates = await self.get_candidates_within_radius(
            latitude=request.latitude,
            longitude=request.longitude,
            preference_vector=user_preference_vector,
        )
        if not candidates:
            return MapSearchResponse()

        candidate_ids = [candidate.cafe_id for candidate in candidates]
        menus_by_cafe = await self.get_cafe_menus(candidate_ids)
        query_similarity_scores = await self.get_query_similarity_scores(
            candidate_ids,
            processed_query.vector,
        )
        ranked_cafe_ids = self.rank_cafes(
            candidates=candidates,
            menus_by_cafe=menus_by_cafe,
            normalized_keyword=processed_query.normalized_query,
            mood_keywords=mood_keywords,
            query_similarity_scores=query_similarity_scores,
        )
        extracted_menus = self.resolve_extracted_menu_ids(
            normalized_query=processed_query.normalized_query,
            menu_phrases=processed_query.menu_phrases,
            menus_by_cafe=menus_by_cafe,
            ranked_cafe_ids=ranked_cafe_ids,
        )

        cafes = {
            str(cafe_id): rank
            for rank, cafe_id in enumerate(ranked_cafe_ids[:_MAX_RESULTS], start=1)
        }

        return MapSearchResponse(cafes=cafes, extracted_menus=extracted_menus)

    async def get_candidates_within_radius(
        self,
        *,
        latitude: float,
        longitude: float,
        preference_vector: list[float],
    ) -> list[CafeCandidate]:
        pool = get_pg_pool()
        vector_literal = self.to_vector_literal(preference_vector)

        async with pool.acquire() as conn:
            rows = await conn.fetch(
                _RADIUS_CAFE_QUERY,
                vector_literal,
                longitude,
                latitude,
                _RADIUS_METERS,
            )

        return [
            CafeCandidate(
                cafe_id=UUID(str(row["cafe_id"])),
                preference_similarity=self.clamp_similarity(row["preference_similarity"]),
            )
            for row in rows
        ]

    async def get_query_similarity_scores(
        self,
        candidate_ids: list[UUID],
        query_vector: list[float],
    ) -> dict[UUID, float]:
        if not query_vector:
            return {}

        pool = get_pg_pool()
        vector_literal = self.to_vector_literal(query_vector)

        async with pool.acquire() as conn:
            rows = await conn.fetch(_QUERY_SIMILARITY_QUERY, vector_literal, candidate_ids)

        return {
            UUID(str(row["cafe_id"])): self.clamp_similarity(row["query_similarity"])
            for row in rows
        }

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

    def rank_cafes(
        self,
        *,
        candidates: list[CafeCandidate],
        menus_by_cafe: dict[UUID, list[CafeMenu]],
        normalized_keyword: str,
        mood_keywords: list[str],
        query_similarity_scores: dict[UUID, float],
    ) -> list[UUID]:
        keyword_terms = self.build_keyword_terms(normalized_keyword, mood_keywords)
        scored_candidates: list[tuple[float, float, float, str, UUID]] = []

        for candidate in candidates:
            keyword_score = self.score_cafe_menus(
                keyword_terms,
                menus_by_cafe.get(candidate.cafe_id, []),
            )
            query_similarity = query_similarity_scores.get(candidate.cafe_id, 0.0)
            final_score = (
                0.5 * candidate.preference_similarity
                + 0.2 * query_similarity
                + 0.3 * keyword_score
            )
            scored_candidates.append(
                (
                    final_score,
                    candidate.preference_similarity,
                    keyword_score,
                    str(candidate.cafe_id),
                    candidate.cafe_id,
                )
            )

        scored_candidates.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))
        return [item[4] for item in scored_candidates]

    def resolve_extracted_menu_ids(
        self,
        *,
        normalized_query: str,
        menu_phrases: list[str],
        menus_by_cafe: dict[UUID, list[CafeMenu]],
        ranked_cafe_ids: list[UUID],
    ) -> dict[str, int]:
        phrase_counts = self.collect_menu_phrase_counts(
            normalized_query=normalized_query,
            menu_phrases=menu_phrases,
            menus_by_cafe=menus_by_cafe,
        )
        resolved_menu_counts: Counter[str] = Counter()

        for phrase, occurrence_count in phrase_counts.items():
            representative_menu_id = self.pick_representative_menu_id(
                phrase=phrase,
                menus_by_cafe=menus_by_cafe,
                ranked_cafe_ids=ranked_cafe_ids,
            )
            if representative_menu_id is None:
                continue
            resolved_menu_counts[str(representative_menu_id)] += occurrence_count

        return dict(resolved_menu_counts)

    def collect_menu_phrase_counts(
        self,
        *,
        normalized_query: str,
        menu_phrases: list[str],
        menus_by_cafe: dict[UUID, list[CafeMenu]],
    ) -> Counter[str]:
        phrase_counts: Counter[str] = Counter()
        known_phrase_keys: set[str] = set()

        for phrase in menu_phrases:
            normalized_phrase = phrase.strip()
            if not normalized_phrase:
                continue
            phrase_counts[normalized_phrase] += 1
            known_phrase_keys.add(normalized_phrase.casefold())

        query_text = normalized_query.casefold()
        menu_names: dict[str, str] = {}
        for menus in menus_by_cafe.values():
            for menu in menus:
                normalized_menu_name = menu.menu_name.strip()
                if not normalized_menu_name:
                    continue
                menu_key = normalized_menu_name.casefold()
                menu_names.setdefault(menu_key, normalized_menu_name)

        for menu_key, menu_name in menu_names.items():
            if menu_key in known_phrase_keys:
                continue
            occurrence_count = query_text.count(menu_key)
            if occurrence_count > 0:
                phrase_counts[menu_name] += occurrence_count

        return phrase_counts

    def pick_representative_menu_id(
        self,
        *,
        phrase: str,
        menus_by_cafe: dict[UUID, list[CafeMenu]],
        ranked_cafe_ids: list[UUID],
    ) -> int | None:
        phrase_key = phrase.casefold()

        for cafe_id in ranked_cafe_ids:
            for menu in menus_by_cafe.get(cafe_id, []):
                if menu.menu_name.casefold() == phrase_key:
                    return menu.menu_id

        for cafe_id in ranked_cafe_ids:
            for menu in menus_by_cafe.get(cafe_id, []):
                if phrase_key and phrase_key in menu.menu_name.casefold():
                    return menu.menu_id

        for cafe_id in ranked_cafe_ids:
            for menu in menus_by_cafe.get(cafe_id, []):
                if phrase_key and phrase_key in (menu.menu_description or "").casefold():
                    return menu.menu_id

        return None

    def build_keyword_terms(
        self,
        normalized_keyword: str,
        mood_keywords: list[str],
    ) -> list[str]:
        keyword_terms: list[str] = []
        if normalized_keyword:
            keyword_terms.append(normalized_keyword.casefold())
            keyword_terms.extend(self.tokenize(normalized_keyword))
        for mood_keyword in mood_keywords:
            keyword_terms.append(mood_keyword.casefold())
            keyword_terms.extend(self.tokenize(mood_keyword))

        deduplicated_terms: list[str] = []
        seen_terms: set[str] = set()
        for term in keyword_terms:
            normalized_term = term.strip()
            if not normalized_term or normalized_term in seen_terms:
                continue
            seen_terms.add(normalized_term)
            deduplicated_terms.append(normalized_term)
        return deduplicated_terms

    def score_cafe_menus(
        self,
        keyword_terms: list[str],
        menus: list[CafeMenu],
    ) -> float:
        if not keyword_terms or not menus:
            return 0.0

        score = 0.0
        for term in keyword_terms:
            for menu in menus:
                score += menu.menu_name.casefold().count(term) * 2.0
                score += (menu.menu_description or "").casefold().count(term)

        return min(score / len(keyword_terms), 1.0)

    def resolve_mood_keywords(self, mood: list[int]) -> list[str]:
        _ = mood
        return []

    def tokenize(self, text: str) -> list[str]:
        return [token.casefold() for token in re.split(r"\s+", text) if token.strip()]

    def clamp_similarity(self, value: object) -> float:
        if value is None:
            return 0.0
        numeric_value = float(value)
        return max(0.0, min(numeric_value, 1.0))

    def to_vector_literal(self, vector: list[float]) -> str:
        return "[" + ",".join(str(value) for value in vector) + "]"
