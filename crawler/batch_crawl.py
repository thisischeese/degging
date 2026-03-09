"""
batch_crawl.py – cafes.json에서 N개 카페를 순차 크롤링

Usage:
    python batch_crawl.py              # 처음 100개
    python batch_crawl.py --limit 50   # 처음 50개
    python batch_crawl.py --offset 100 --limit 100  # 101~200번째
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

from crawler import run_crawl, OUTPUT_DIR

DATA_DIR  = Path(__file__).parent / "data"
CAFE_JSON = DATA_DIR / "cafes.json"
LOG_FILE  = DATA_DIR / "batch_crawl_log.jsonl"


def load_cafes(offset: int, limit: int) -> list[str]:
    cafes = json.loads(CAFE_JSON.read_text(encoding="utf-8"))
    return cafes[offset : offset + limit]


def already_crawled(name: str) -> bool:
    base = OUTPUT_DIR / name
    if not base.exists():
        return False
    texts_dir = base / "texts"
    return texts_dir.exists() and any(texts_dir.iterdir())


def log(entry: dict) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def crawl_all(cafes: list[str]) -> None:
    total   = len(cafes)
    success = 0
    skipped = 0
    failed  = 0

    for i, name in enumerate(cafes, 1):
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

        # 요청 간격: 서버 부하 방지
        await asyncio.sleep(2)

    print(f"\n{'='*50}")
    print(f"완료: 성공={success}  스킵={skipped}  실패={failed}  합계={total}")
    print(f"로그: {LOG_FILE}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", type=int, default=0,   help="시작 인덱스 (기본 0)")
    parser.add_argument("--limit",  type=int, default=100, help="크롤링 개수 (기본 100)")
    args = parser.parse_args()

    cafes = load_cafes(args.offset, args.limit)
    print(f"크롤링 대상: {args.offset}~{args.offset + len(cafes) - 1}번  ({len(cafes)}개)")
    print(f"출력 경로:   {OUTPUT_DIR}")
    print(f"로그 파일:   {LOG_FILE}\n")

    asyncio.run(crawl_all(cafes))


if __name__ == "__main__":
    main()
