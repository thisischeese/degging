from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from uuid import UUID

from app.core.config import settings
from app.db.postgresql import get_pg_pool
from app.models.map_search import MapSearchRequest, MapSearchResponse
from app.services.discovery_service import UserPreferenceNotFoundError
from app.services.query_preprocess_service import QueryPreprocessService

_RADIUS_METERS = 2000
_MAX_RESULTS = settings.discovery_top_k
_MOOD_KEYWORDS: dict[int, tuple[str, ...]] = {
    0: ("우드톤", "따뜻함", "따뜻한", "아늑한", "포근한"),
    1: ("식물원", "플랜테리어", "식물", "초록", "녹음"),
    2: ("힙한", "힙", "트렌디", "감성", "감각적인"),
    3: ("조용한", "조용", "차분한", "차분", "고요한"),
    4: ("탁트인", "탁 트인", "뷰 좋은", "뷰", "전망", "창가"),
}

_USER_PREFERENCE_QUERY = """
    SELECT preference_vector::text AS preference_vector
    FROM user_preference
    WHERE user_id = $1
"""

_RADIUS_CAFE_QUERY = """
    SELECT
        cafe_id,
        name,
        address,
        road_address,
        cafe_intro,
        "brandName" AS brand_name,
        "branchName" AS branch_name,
        1 - (cafe_vector <=> $1::vector) AS preference_similarity
    FROM cafes
    WHERE cafe_vector IS NOT NULL
      AND ST_DWithin(
          location,
          ST_SetSRID(ST_MakePoint($2, $3), 4326)::geography,
          $4
      )
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


class MapSearchService:
    def __init__(
        self,
        query_preprocess_service: QueryPreprocessService | None = None,
    ) -> None:
        self._query_preprocess_service = query_preprocess_service or QueryPreprocessService()

    async def search(self, request: MapSearchRequest) -> MapSearchResponse:
        processed_query = await self._query_preprocess_service.preprocess(request.keyword)
        mood_keywords = self.resolve_mood_keywords(request.mood)
        user_preference_vector = await self.get_user_preference_vector(request.user_id)

        candidates = await self.get_candidates_within_radius(
            latitude=request.latitude,
            longitude=request.longitude,
            preference_vector=user_preference_vector,
        )
        if not candidates:
            return MapSearchResponse()

        candidate_ids = [candidate.cafe_id for candidate in candidates]
        menus_by_cafe = await self.get_cafe_menus(candidate_ids)
        ranked_cafe_ids = self.rank_cafes(
            candidates=candidates,
            menus_by_cafe=menus_by_cafe,
            normalized_keyword=processed_query.normalized_query,
            mood_keywords=mood_keywords,
        )
        if not ranked_cafe_ids:
            return MapSearchResponse()

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

    async def get_user_preference_vector(self, user_id: UUID) -> list[float]:
        pool = get_pg_pool()

        async with pool.acquire() as conn:
            row = await conn.fetchrow(_USER_PREFERENCE_QUERY, user_id)

        if row is None or row["preference_vector"] is None:
            raise UserPreferenceNotFoundError(f"user_id={user_id} preference vector not found.")

        preference_vector = self.parse_vector_literal(row["preference_vector"])
        if not preference_vector:
            raise UserPreferenceNotFoundError(f"user_id={user_id} preference vector not found.")

        return preference_vector

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

    def rank_cafes(
        self,
        *,
        candidates: list[CafeCandidate],
        menus_by_cafe: dict[UUID, list[CafeMenu]],
        normalized_keyword: str,
        mood_keywords: list[str],
    ) -> list[UUID]:
        keyword_terms = self.build_keyword_terms(normalized_keyword)
        mood_terms = self.build_keyword_terms(" ".join(mood_keywords))
        scored_candidates: list[tuple[float, float, str, UUID]] = []

        for candidate in candidates:
            searchable_text = self.build_searchable_text(
                candidate,
                menus_by_cafe.get(candidate.cafe_id, []),
            )
            keyword_score = self.score_text_terms(keyword_terms, searchable_text)
            mood_score = self.score_text_terms(mood_terms, searchable_text)

            if keyword_terms and keyword_score == 0.0:
                continue
            if mood_terms and mood_score == 0.0:
                continue

            lexical_score = keyword_score + mood_score
            scored_candidates.append(
                (
                    candidate.preference_similarity,
                    lexical_score,
                    str(candidate.cafe_id),
                    candidate.cafe_id,
                )
            )

        scored_candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
        return [item[3] for item in scored_candidates]

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

    def resolve_mood_keywords(self, mood: list[int]) -> list[str]:
        resolved_keywords: list[str] = []
        seen_keywords: set[str] = set()

        for mood_id in mood:
            for keyword in _MOOD_KEYWORDS.get(mood_id, ()):
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
            text_parts.append(menu.menu_description or "")
        return " ".join(part for part in text_parts if part).casefold()

    def score_text_terms(self, terms: list[str], searchable_text: str) -> float:
        if not terms or not searchable_text:
            return 0.0

        return sum(searchable_text.count(term) for term in terms)

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
        return "[" + ",".join(str(value) for value in vector) + "]"

    def parse_vector_literal(self, vector_literal: str) -> list[float]:
        normalized_literal = vector_literal.strip()
        if not normalized_literal or normalized_literal == "[]":
            return []
        if not (normalized_literal.startswith("[") and normalized_literal.endswith("]")):
            raise ValueError(f"Invalid vector literal: {vector_literal}")

        values = normalized_literal[1:-1].strip()
        if not values:
            return []

        return [float(value.strip()) for value in values.split(",") if value.strip()]
