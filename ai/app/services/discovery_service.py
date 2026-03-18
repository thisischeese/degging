"""
Discovery 탭 서비스
- MongoDB에서 사용자 취향 벡터(u_rt) 조회
- PostgreSQL pgvector ANN 인덱스로 유사 카페 top-100 검색
"""

from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.db.postgresql import get_pg_pool


# MongoDB 컬렉션 이름
_USER_PREFERENCE_COLLECTION = "user_preferences"

# PostgreSQL 카페 임베딩 테이블
# DDL 참고:
#   CREATE TABLE cafe_embeddings (
#       cafe_id uuid NOT NULL REFERENCES cafes(cafe_id),
#       embedding vector(768) NOT NULL
#   );
#   CREATE INDEX cafe_embeddings_hnsw_idx
#       ON cafe_embeddings USING hnsw (embedding vector_cosine_ops);
_CAFE_ANN_QUERY = """
    SELECT cafe_id
    FROM cafe_embeddings
    ORDER BY embedding <=> $1::vector
    LIMIT $2
"""


class UserPreferenceNotFoundError(Exception):
    """MongoDB에 사용자 취향 벡터가 없을 때"""


class DiscoveryService:
    def __init__(self, mongo_db: AsyncIOMotorDatabase) -> None:
        self._mongo_db = mongo_db

    async def get_user_preference_vector(self, user_id: UUID) -> list[float]:
        """
        MongoDB에서 사용자 실시간 취향 벡터(u_rt)를 조회한다.

        컬렉션 문서 구조:
        {
            "user_id": "<uuid-string>",
            "u_rt": [0.1, 0.2, ...],   # 768차원 float 배열
            ...
        }
        """
        collection = self._mongo_db[_USER_PREFERENCE_COLLECTION]
        doc = await collection.find_one(
            {"user_id": str(user_id)},
            projection={"u_rt": 1, "_id": 0},
        )
        if doc is None or not doc.get("u_rt"):
            raise UserPreferenceNotFoundError(
                f"user_id={user_id} 에 대한 취향 벡터가 없습니다."
            )
        return doc["u_rt"]

    async def get_top_cafes_by_vector(
        self,
        preference_vector: list[float],
        top_k: int = settings.discovery_top_k,
    ) -> list[UUID]:
        """
        PostgreSQL pgvector HNSW 인덱스를 사용해 코사인 유사도 기준
        상위 top_k 개 카페 ID를 반환한다.
        """
        pool = get_pg_pool()
        # pgvector는 '[0.1,0.2,...]' 형태의 문자열 또는 list를 받는다
        vector_literal = "[" + ",".join(str(v) for v in preference_vector) + "]"

        async with pool.acquire() as conn:
            rows = await conn.fetch(_CAFE_ANN_QUERY, vector_literal, top_k)

        return [UUID(str(row["cafe_id"])) for row in rows]

    async def discover(self, user_id: UUID) -> list[UUID]:
        """
        사용자 취향 벡터를 조회하고 유사 카페 top-100을 반환한다.
        """
        preference_vector = await self.get_user_preference_vector(user_id)
        return await self.get_top_cafes_by_vector(preference_vector)
