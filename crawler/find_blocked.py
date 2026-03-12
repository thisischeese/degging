"""
find_blocked.py – 차단된 크롤링 결과를 탐지하고 재크롤링 목록을 생성한다.

Usage:
    python find_blocked.py              # 차단 현황 출력 + blocked_cafes.json 생성
    python find_blocked.py --clean      # 차단된 폴더 내 텍스트 파일 삭제 (재크롤링 가능 상태로)
"""

import argparse
import json
from pathlib import Path

from crawler import OUTPUT_DIR, BLOCK_MARKER

DATA_DIR = Path(__file__).parent / "data"


def find_blocked() -> list[str]:
    """차단 메시지가 저장된 카페 폴더 이름 목록을 반환한다."""
    blocked = []
    for texts_dir in sorted(OUTPUT_DIR.glob("*/texts")):
        home = texts_dir / "home.txt"
        if not home.exists():
            continue
        try:
            if BLOCK_MARKER in home.read_text(encoding="utf-8"):
                blocked.append(texts_dir.parent.name)
        except OSError:
            pass
    return blocked


def clean_blocked(blocked: list[str]) -> None:
    """차단된 폴더의 텍스트 파일을 삭제해 재크롤링 가능 상태로 초기화한다."""
    for name in blocked:
        texts_dir = OUTPUT_DIR / name / "texts"
        if texts_dir.exists():
            for f in texts_dir.glob("*.txt"):
                f.unlink()
            print(f"  초기화: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--clean",
        action="store_true",
        help="차단된 폴더의 텍스트 파일을 삭제해 재크롤링 가능 상태로 초기화",
    )
    args = parser.parse_args()

    blocked = find_blocked()

    print(f"\n차단 감지 결과: {len(blocked)}개\n")
    for name in blocked:
        print(f"  - {name}")

    out = DATA_DIR / "blocked_cafes.json"
    out.write_text(json.dumps(blocked, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n목록 저장: {out}")

    if args.clean:
        print("\n차단 폴더 초기화 중...")
        clean_blocked(blocked)
        print("완료. batch_crawl_resume.py 를 blocked_cafes.json 으로 실행하세요.")
    else:
        print("\n--clean 옵션을 추가하면 차단 폴더를 초기화합니다.")
        print("이후 batch_crawl_resume.py 에서 blocked_cafes.json 을 사용해 재크롤링하세요.")


if __name__ == "__main__":
    main()
