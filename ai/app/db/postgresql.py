import asyncpg
from app.core.config import settings

_pool: asyncpg.Pool | None = None


async def connect_postgresql() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=str(settings.postgres_dsn),
        min_size=settings.postgres_pool_min_size,
        max_size=settings.postgres_pool_max_size,
    )


async def close_postgresql() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pg_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("PostgreSQL pool is not initialized")
    return _pool
