import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.db import mongodb, postgresql


class PostgreSQLRuntimeConfigTest(unittest.IsolatedAsyncioTestCase):
    async def test_connect_postgresql_uses_configured_pool_sizes(self) -> None:
        fake_pool = AsyncMock()

        with (
            patch.object(postgresql.settings, "postgres_pool_min_size", 1),
            patch.object(postgresql.settings, "postgres_pool_max_size", 5),
            patch("app.db.postgresql.asyncpg.create_pool", new=AsyncMock(return_value=fake_pool)) as create_pool,
        ):
            await postgresql.connect_postgresql()

        create_pool.assert_awaited_once_with(
            dsn=str(postgresql.settings.postgres_dsn),
            min_size=1,
            max_size=5,
        )

        await postgresql.close_postgresql()
        fake_pool.close.assert_awaited_once()


class MongoRuntimeConfigTest(unittest.IsolatedAsyncioTestCase):
    async def test_connect_mongodb_uses_configured_max_pool_size(self) -> None:
        fake_client = MagicMock()

        with (
            patch.object(mongodb.settings, "mongo_max_pool_size", 20),
            patch("app.db.mongodb.AsyncIOMotorClient", return_value=fake_client) as client_cls,
        ):
            await mongodb.connect_mongodb()

        client_cls.assert_called_once_with(
            str(mongodb.settings.mongo_uri),
            maxPoolSize=20,
        )

        await mongodb.close_mongodb()
        fake_client.close.assert_called_once()
