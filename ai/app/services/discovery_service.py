from dataclasses import dataclass
from uuid import UUID

from app.core.config import settings
from app.db.postgresql import get_pg_pool
from app.services.preference_vector import (
    UserPreferenceNotFoundError,
    fetch_user_preference_vector,
    to_vector_literal,
)

_DISCOVERY_CAFE_QUERY = """
    SELECT
        cafe_id,
        name
    FROM cafes
    WHERE cafe_vector IS NOT NULL
    ORDER BY cafe_vector <=> $1::vector
    LIMIT $2
"""


@dataclass(slots=True)
class RecommendedCafe:
    cafe_id: UUID
    name: str | None


def _normalize_cafe_name(value: object) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


class DiscoveryService:
    async def get_user_preference_vector(self, user_id: UUID) -> list[float]:
        pool = get_pg_pool()
        async with pool.acquire() as conn:
            return await fetch_user_preference_vector(conn, user_id)

    async def get_top_cafes_by_vector(
        self,
        preference_vector: list[float],
        top_k: int = settings.discovery_top_k,
    ) -> list[RecommendedCafe]:
        pool = get_pg_pool()
        async with pool.acquire() as conn:
            return await self._fetch_top_cafes_by_vector(conn, preference_vector, top_k)

    async def discover(self, user_id: UUID) -> list[RecommendedCafe]:
        pool = get_pg_pool()
        async with pool.acquire() as conn:
            preference_vector = await fetch_user_preference_vector(conn, user_id)
            return await self._fetch_top_cafes_by_vector(
                conn,
                preference_vector,
                settings.discovery_top_k,
            )

    async def _fetch_top_cafes_by_vector(
        self,
        conn,
        preference_vector: list[float],
        top_k: int,
    ) -> list[RecommendedCafe]:
        rows = await conn.fetch(
            _DISCOVERY_CAFE_QUERY,
            to_vector_literal(preference_vector),
            top_k,
        )
        return [
            RecommendedCafe(
                cafe_id=UUID(str(row["cafe_id"])),
                name=_normalize_cafe_name(row["name"]),
            )
            for row in rows
        ]
