"""
pipeline.py – 3단계 자동 파이프라인

  [1단계] 차단된 카페 감지 → 폴더 초기화 → 재크롤링
  [2단계] 100개 전체 검증 (차단 여부 + 내용 유효성)
  [3단계] 검증 통과 시 CSV 4종 내보내기

Usage:
    python pipeline.py               # cafes.json 처음 100개 기준
    python pipeline.py --limit 50    # 처음 50개만
    python pipeline.py --offset 100 --limit 100  # 101~200번째
    python pipeline.py --csv-only    # 크롤링 건너뛰고 CSV만 재생성
"""

import argparse
import asyncio
import json
import random
import sys
import time
from pathlib import Path

from crawler import run_crawl, OUTPUT_DIR, BLOCK_MARKER
from to_csv import (
    process_cafe,
    write_csv,
    PLACE_COLS, MENU_COLS, VISITOR_REVIEW_COLS, BLOG_REVIEW_COLS,
    DATA_DIR,
)

CAFE_JSON = Path(__file__).parent / "data" / "cafes.json"
LOG_FILE  = DATA_DIR / "pipeline_log.jsonl"

# 검증 기준: home.txt 최소 줄 수 (차단 메시지는 보통 5줄 이하)
MIN_VALID_LINES = 10


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def load_cafes(offset: int, limit: int) -> list[str]:
    return json.loads(CAFE_JSON.read_text(encoding="utf-8"))[offset: offset + limit]


def log(entry: dict) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _texts_dir(name: str) -> Path:
    return OUTPUT_DIR / name / "texts"


# ── 단계 1: 차단 감지 + 재크롤링 ─────────────────────────────────────────────

def find_blocked_or_missing(cafes: list[str]) -> list[str]:
    """차단되었거나 아직 크롤링되지 않은 카페 목록을 반환한다."""
    targets: list[str] = []
    for name in cafes:
        td = _texts_dir(name)
        if not td.exists() or not any(td.iterdir()):
            targets.append(name)
            continue
        home = td / "home.txt"
        if not home.exists():
            targets.append(name)
            continue
        try:
            content = home.read_text(encoding="utf-8")
            if BLOCK_MARKER in content:
                targets.append(name)
        except OSError:
            targets.append(name)
    return targets


def clean_cafe(name: str) -> None:
    """해당 카페의 texts/*.txt 파일을 삭제해 재크롤링 가능 상태로 초기화한다."""
    td = _texts_dir(name)
    if td.exists():
        for f in td.glob("*.txt"):
            f.unlink()


async def recrawl(targets: list[str]) -> dict[str, str]:
    """targets 목록을 순차 재크롤링한다. {name: "ok"|"fail"} 반환."""
    results: dict[str, str] = {}
    total = len(targets)

    for i, name in enumerate(targets, 1):
        clean_cafe(name)
        print(f"\n  [{i:3d}/{total}] 재크롤링: {name}")
        t0 = time.time()
        try:
            await run_crawl(search_name=name)
            elapsed = round(time.time() - t0, 1)
            print(f"    OK ({elapsed}s)")
            log({"phase": "recrawl", "name": name, "status": "ok", "elapsed": elapsed})
            results[name] = "ok"
        except Exception as e:
            elapsed = round(time.time() - t0, 1)
            msg = str(e)[:120]
            print(f"    FAIL: {msg}", file=sys.stderr)
            log({"phase": "recrawl", "name": name, "status": "fail", "error": msg, "elapsed": elapsed})
            results[name] = "fail"

        if i < total:
            delay = random.uniform(15.0, 40.0)
            if i % 10 == 0:
                delay += random.uniform(60.0, 120.0)
                print(f"  [휴식] 10개 완료 → {delay:.0f}초 대기")
            else:
                print(f"  [대기] {delay:.1f}초")
            await asyncio.sleep(delay)

    return results


# ── 단계 2: 검증 ──────────────────────────────────────────────────────────────

class VerifyResult:
    def __init__(self):
        self.ok:      list[str] = []
        self.blocked: list[str] = []
        self.missing: list[str] = []
        self.too_short: list[str] = []

    @property
    def all_passed(self) -> bool:
        return not (self.blocked or self.missing or self.too_short)

    def summary(self) -> str:
        return (
            f"통과: {len(self.ok)}개  "
            f"차단: {len(self.blocked)}개  "
            f"미수집: {len(self.missing)}개  "
            f"내용부족: {len(self.too_short)}개"
        )


def verify_all(cafes: list[str]) -> VerifyResult:
    """cafes 목록 전체의 크롤링 결과를 검증한다."""
    vr = VerifyResult()

    for name in cafes:
        td = _texts_dir(name)
        home = td / "home.txt"

        if not td.exists() or not home.exists():
            vr.missing.append(name)
            continue

        try:
            content = home.read_text(encoding="utf-8")
        except OSError:
            vr.missing.append(name)
            continue

        if BLOCK_MARKER in content:
            vr.blocked.append(name)
            continue

        line_count = len([l for l in content.splitlines() if l.strip()])
        if line_count < MIN_VALID_LINES:
            vr.too_short.append(name)
            continue

        vr.ok.append(name)

    return vr


def print_verify_report(vr: VerifyResult) -> None:
    print(f"\n{'─'*50}")
    print(f"[검증 결과] {vr.summary()}")
    if vr.blocked:
        print(f"\n  차단된 카페 ({len(vr.blocked)}개):")
        for n in vr.blocked:
            print(f"    - {n}")
    if vr.missing:
        print(f"\n  미수집 카페 ({len(vr.missing)}개):")
        for n in vr.missing:
            print(f"    - {n}")
    if vr.too_short:
        print(f"\n  내용 부족 카페 ({len(vr.too_short)}개):")
        for n in vr.too_short:
            print(f"    - {n}")
    print(f"{'─'*50}")


# ── 단계 3: CSV 내보내기 ──────────────────────────────────────────────────────

def export_csv(cafes: list[str]) -> None:
    """cafes 목록에 해당하는 카페만 CSV로 내보낸다."""
    target_set = set(cafes)

    all_places: list[dict] = []
    all_menus:  list[dict] = []
    all_vr:     list[dict] = []
    all_br:     list[dict] = []

    skipped = 0
    for cafe_dir in sorted(OUTPUT_DIR.iterdir()):
        if not cafe_dir.is_dir():
            continue
        if cafe_dir.name not in target_set:
            continue

        result = process_cafe(cafe_dir)
        if result is None:
            skipped += 1
            continue

        place_row, menu_rows, vr_rows, br_rows = result
        all_places.append(place_row)
        all_menus.extend(menu_rows)
        all_vr.extend(vr_rows)
        all_br.extend(br_rows)

        print(
            f"  [{cafe_dir.name}] "
            f"메뉴:{len(menu_rows)}  방문리뷰:{len(vr_rows)}  블로그:{len(br_rows)}"
        )

    write_csv(DATA_DIR / "place.csv",         PLACE_COLS,          all_places)
    write_csv(DATA_DIR / "menu.csv",           MENU_COLS,           all_menus)
    write_csv(DATA_DIR / "visitor_review.csv", VISITOR_REVIEW_COLS, all_vr)
    write_csv(DATA_DIR / "blog_review.csv",    BLOG_REVIEW_COLS,    all_br)

    print(
        f"\n[CSV 완료] place:{len(all_places)}  menu:{len(all_menus)}  "
        f"visitor_review:{len(all_vr)}  blog_review:{len(all_br)}  "
        f"스킵:{skipped}"
    )
    if skipped:
        print(f"  ※ texts 폴더 없음 등으로 {skipped}개 카페가 CSV에서 제외되었습니다.")
    print(f"  저장 위치: {DATA_DIR}/")


# ── 메인 ─────────────────────────────────────────────────────────────────────

async def run(offset: int, limit: int, csv_only: bool) -> None:
    cafes = load_cafes(offset, limit)
    print(f"대상 카페: {len(cafes)}개 (offset={offset}, limit={limit})")

    # ── 단계 1: 재크롤링 ──────────────────────────────────────────────────────
    if not csv_only:
        print(f"\n{'='*50}")
        print("[단계 1] 차단/미수집 카페 감지 및 재크롤링")
        targets = find_blocked_or_missing(cafes)

        if not targets:
            print("  재크롤링 대상 없음. 모든 카페가 정상 수집 상태입니다.")
        else:
            print(f"  재크롤링 대상: {len(targets)}개")
            for n in targets:
                print(f"    - {n}")
            recrawl_results = await recrawl(targets)
            fail_count = sum(1 for s in recrawl_results.values() if s == "fail")
            print(f"\n  재크롤링 완료: 성공={len(targets)-fail_count}  실패={fail_count}")
    else:
        print("\n[단계 1] --csv-only 모드: 재크롤링 건너뜀")

    # ── 단계 2: 검증 ──────────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print("[단계 2] 전체 검증")
    vr = verify_all(cafes)
    print_verify_report(vr)
    log({"phase": "verify", "summary": vr.summary(), "blocked": vr.blocked,
         "missing": vr.missing, "too_short": vr.too_short})

    if not vr.all_passed:
        print(
            "\n[경고] 일부 카페가 검증을 통과하지 못했습니다.\n"
            "  - 해당 카페는 CSV에서 제외됩니다.\n"
            "  - 재실행하면 실패한 카페만 다시 크롤링 시도합니다.\n"
            "  → 계속해서 CSV를 생성합니다 (통과한 카페만 포함)."
        )

    # ── 단계 3: CSV 내보내기 ──────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print("[단계 3] CSV 내보내기")
    export_csv(vr.ok)

    print(f"\n{'='*50}")
    if vr.all_passed:
        print(f"[완료] 전체 {len(cafes)}개 카페 정상 처리 및 CSV 저장 완료.")
    else:
        failed_names = vr.blocked + vr.missing + vr.too_short
        print(f"[부분 완료] {len(vr.ok)}/{len(cafes)}개 카페 CSV 저장.")
        print(f"  미처리 {len(failed_names)}개: {failed_names[:5]}{'...' if len(failed_names)>5 else ''}")
        print("  python pipeline.py 를 다시 실행하면 미처리 카페를 재시도합니다.")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="크롤링 → 검증 → CSV 파이프라인")
    parser.add_argument("--offset",   type=int, default=0,   help="cafes.json 시작 인덱스 (기본 0)")
    parser.add_argument("--limit",    type=int, default=100, help="처리할 카페 수 (기본 100)")
    parser.add_argument("--csv-only", action="store_true",   help="재크롤링 건너뛰고 CSV만 재생성")
    args = parser.parse_args()

    asyncio.run(run(args.offset, args.limit, args.csv_only))


if __name__ == "__main__":
    main()
