"""
batch_crawl_resume.py – missing_cafes.json의 미완료 카페를 순차 크롤링
"""
import asyncio
import json
import sys
import time
from pathlib import Path

from crawler import run_crawl, OUTPUT_DIR

DATA_DIR  = Path(__file__).parent / "data"
LOG_FILE  = DATA_DIR / "batch_crawl_log.jsonl"


def already_crawled(name: str) -> bool:
    base = OUTPUT_DIR / name
    texts_dir = base / "texts"
    return texts_dir.exists() and any(texts_dir.iterdir())


def log(entry: dict) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def main() -> None:
    missing = json.loads((DATA_DIR / "missing_cafes.json").read_text(encoding="utf-8"))
    total   = len(missing)
    success = skipped = failed = 0

    print(f"재시도 대상: {total}개\n")

    for i, name in enumerate(missing, 1):
        prefix = f"[{i:3d}/{total}]"

        if already_crawled(name):
            print(f"{prefix} SKIP  {name}")
            skipped += 1
            continue

        print(f"\n{prefix} START {name}")
        t0 = time.time()
        try:
            await run_crawl(search_name=name)
            elapsed = round(time.time() - t0, 1)
            print(f"{prefix} OK    {name}  ({elapsed}s)")
            log({"name": name, "status": "ok", "elapsed": elapsed})
            success += 1
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            msg = str(e)[:120]
            print(f"{prefix} FAIL  {name}  {msg}", file=sys.stderr)
            log({"name": name, "status": "fail", "error": msg, "elapsed": elapsed})
            failed += 1

        await asyncio.sleep(2)

    print(f"\n{'='*50}")
    print(f"완료: 성공={success}  스킵={skipped}  실패={failed}")


if __name__ == "__main__":
    asyncio.run(main())
