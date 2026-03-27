from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from app.db.postgresql import close_postgresql, connect_postgresql, get_pg_pool
from app.services.menu_query_encoder import (
    build_menu_encoder_and_records,
    resolve_menu_query_encoder_path,
)

_EXPORT_MENU_ROWS_QUERY = """
    SELECT
        cafe_id,
        menu_id,
        menu_name,
        menu_description
    FROM cafe_menus
    ORDER BY menu_id
"""

logger = logging.getLogger("uvicorn.error")


def resolve_menu_vector_export_path() -> Path:
    return resolve_menu_query_encoder_path().with_name("menu_search_vectors.json")


async def fetch_menu_rows() -> list[dict[str, Any]]:
    pool = get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(_EXPORT_MENU_ROWS_QUERY)
    return [dict(row) for row in rows]


async def export_menu_search_artifacts() -> tuple[Path, Path]:
    rows = await fetch_menu_rows()
    logger.info("menu_search_artifact_export_started: menu_row_count=%s", len(rows))
    artifact_path, records = build_menu_encoder_and_records(rows)
    export_path = resolve_menu_vector_export_path()
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(
        "menu_search_artifact_export_completed: artifact_path=%s export_path=%s record_count=%s",
        artifact_path,
        export_path,
        len(records),
    )
    return artifact_path, export_path


async def _main() -> None:
    await connect_postgresql()
    try:
        artifact_path, export_path = await export_menu_search_artifacts()
        print(f"Menu query encoder written to {artifact_path}")
        print(f"Menu search vectors written to {export_path}")
    finally:
        await close_postgresql()


if __name__ == "__main__":
    asyncio.run(_main())
