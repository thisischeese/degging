from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

_client: AsyncIOMotorClient | None = None


async def connect_mongodb() -> None:
    global _client
    _client = AsyncIOMotorClient(
        str(settings.mongo_uri),
        maxPoolSize=settings.mongo_max_pool_size,
    )


async def close_mongodb() -> None:
    global _client
    if _client:
        _client.close()
        _client = None


def get_mongo_db() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized")
    return _client[settings.mongo_database]
