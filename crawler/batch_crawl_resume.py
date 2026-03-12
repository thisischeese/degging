"""
batch_crawl_resume.py – JSON 목록 파일의 카페를 순차 크롤링

Usage:
    python batch_crawl_resume.py                          # missing_cafes.json (기본값)
    python batch_crawl_resume.py --input blocked_cafes.json  # 차단 목록 재크롤링
"""
import argparse
import asyncio
import json
import random
import sys
import time
from pathlib import Path

from crawler import run_crawl, OUTPUT_DIR, BLOCK_MARKER

DATA_DIR  = Path(__file__).parent / "data"
LOG_FILE  = DATA_DIR / "batch_crawl_log.jsonl"


def already_crawled(name: str) -> bool:
    base = OUTPUT_DIR / name
    texts_dir = base / "texts"
    if not (texts_dir.exists() and any(texts_dir.iterdir())):
        return False
    # 차단 메시지가 저장된 경우 재크롤링 대상
    home = texts_dir / "home.txt"
    if home.exists():
        try:
            if BLOCK_MARKER in home.read_text(encoding="utf-8"):
                return False
        except OSError:
            pass
    return True


def log(entry: dict) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="missing_cafes.json",
        help="크롤링 목록 JSON 파일명 (data/ 하위, 기본: missing_cafes.json)",
    )
    args = parser.parse_args()

    input_file = DATA_DIR / args.input
    missing = json.loads(input_file.read_text(encoding="utf-8"))
    total   = len(missing)
    success = skipped = failed = 0

    print(f"입력 파일: {input_file}")
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

        # 랜덤 딜레이 (봇 패턴 탐지 회피)
        delay = random.uniform(15.0, 40.0)
        if i % 10 == 0:
            delay += random.uniform(60.0, 120.0)
            print(f"  [휴식] 10개 완료 → 추가 대기 포함 총 {delay:.0f}초")
        else:
            print(f"  [대기] {delay:.1f}초")
        await asyncio.sleep(delay)

    print(f"\n{'='*50}")
    print(f"완료: 성공={success}  스킵={skipped}  실패={failed}")


if __name__ == "__main__":
    asyncio.run(main())
