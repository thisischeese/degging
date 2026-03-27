from uuid import UUID

from app.core.config import settings
from app.db.postgresql import get_pg_pool
from app.services.preference_vector import (
    UserPreferenceNotFoundError,
    fetch_user_preference_vector,
    to_vector_literal,
)

_DISCOVERY_CAFE_QUERY = """
    SELECT cafe_id
    FROM cafes
    WHERE cafe_vector IS NOT NULL
    ORDER BY cafe_vector <=> $1::vector
    LIMIT $2
"""


class DiscoveryService:
    async def get_user_preference_vector(self, user_id: UUID) -> list[float]:
        pool = get_pg_pool()
        async with pool.acquire() as conn:
            return await fetch_user_preference_vector(conn, user_id)

    async def get_top_cafes_by_vector(
        self,
        preference_vector: list[float],
        top_k: int = settings.discovery_top_k,
    ) -> list[UUID]:
        pool = get_pg_pool()
        vector_literal = to_vector_literal(preference_vector)

        async with pool.acquire() as conn:
            rows = await conn.fetch(_DISCOVERY_CAFE_QUERY, vector_literal, top_k)

        return [UUID(str(row["cafe_id"])) for row in rows]

    async def discover(self, user_id: UUID) -> list[UUID]:
        pool = get_pg_pool()
        async with pool.acquire() as conn:
            preference_vector = await fetch_user_preference_vector(conn, user_id)
            rows = await conn.fetch(
                _DISCOVERY_CAFE_QUERY,
                to_vector_literal(preference_vector),
                settings.discovery_top_k,
            )

        return [UUID(str(row["cafe_id"])) for row in rows]
