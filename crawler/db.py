"""
db.py – menu.txt 파싱 → cafe_menus 테이블 저장

[menu.txt 구조]
헤더(네비게이션) → 탭 목록(홈/메뉴/리뷰/사진/정보) → 메뉴 항목들 → 푸터

메뉴 항목 패턴:
  [대표 | BEST | NEW ...]  ← 선택적 레이블 (건너뜀)
  메뉴명                   ← 30자 이하 짧은 텍스트
  [설명문]                 ← 선택적 긴 설명 (건너뜀)
  X,XXX원                  ← 가격 (없을 수도 있음)
"""

import asyncio
import re
import uuid
from pathlib import Path

import asyncpg

OUTPUT_DIR = Path(__file__).parent / "output"

DB_DSN = "postgresql://postgres:postgres@localhost:5432/cafe_db"

# 네비게이션 탭 - 이 5개가 모두 나타난 이후부터 메뉴 파싱 시작
NAV_TABS = {"홈", "메뉴", "리뷰", "사진", "정보"}

# 건너뛸 레이블 토큰
LABEL_TOKENS = {"대표", "best", "new", "인기", "추천", "품절", "준비중", "best seller"}

# 가격 패턴: "5,500원" 또는 "5500"
PRICE_RE = re.compile(r"^[\d,]+(원)?$")

# 메뉴 섹션 종료 신호
STOP_PHRASES = ("메뉴 항목과 가격은", "메뉴판 이미지로 보기", "이용약관")


def parse_menu_txt(text: str) -> list[dict]:
    """
    menu.txt 전체 텍스트에서 (메뉴명, 가격) 쌍 목록을 반환한다.
    가격이 없는 메뉴는 price=None 으로 포함.
    """
    lines = [line.strip() for line in text.splitlines()]

    # 네비게이션 탭 5개가 모두 등장한 직후를 파싱 시작점으로 설정
    start_idx = 0
    nav_found: set[str] = set()
    for i, line in enumerate(lines):
        if line in NAV_TABS:
            nav_found.add(line)
            if nav_found == NAV_TABS:
                start_idx = i + 1
                break

    menus: list[dict] = []
    pending_name: str | None = None

    for line in lines[start_idx:]:
        if not line:
            continue

        # 종료 신호
        if any(line.startswith(stop) for stop in STOP_PHRASES):
            break

        # 레이블 건너뜀
        if line.lower() in LABEL_TOKENS:
            continue

        # 가격 라인
        if PRICE_RE.match(line):
            price_str = line.replace("원", "").replace(",", "")
            try:
                price = int(price_str)
            except ValueError:
                price = None
            if pending_name:
                menus.append({"name": pending_name, "price": price})
                pending_name = None
            continue

        # 메뉴명 후보: 30자 이하 짧은 텍스트 (crawler.py JS 로직과 동일 기준)
        if len(line) <= 30:
            if pending_name:
                # 직전 메뉴명에 가격이 없었던 경우
                menus.append({"name": pending_name, "price": None})
            pending_name = line
        # 50자 초과 → 설명문으로 판단, 건너뜀

    # 마지막 메뉴명에 가격이 없는 경우
    if pending_name:
        menus.append({"name": pending_name, "price": None})

    return menus


def cafe_uuid(cafe_name: str) -> uuid.UUID:
    """카페명으로부터 결정적(Deterministic) UUID 생성 (UUID v5)."""
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    return uuid.uuid5(namespace, cafe_name)


async def insert_menus(
    conn: asyncpg.Connection,
    cafe_name: str,
    menus: list[dict],
) -> int:
    """cafe_menus 테이블에 메뉴 목록을 삽입하고 삽입된 행 수를 반환."""
    if not menus:
        return 0

    cid = cafe_uuid(cafe_name)
    rows = [
        (menu["name"], menu["price"], cid)
        for menu in menus
    ]
    await conn.executemany(
        """
        INSERT INTO cafe_menus (menu_id, menu_name, price, cafe_id)
        VALUES (nextval('cafe_menus_menu_id_seq'), $1, $2, $3)
        """,
        rows,
    )
    return len(rows)


async def process_all_menus() -> None:
    """output/ 디렉터리의 모든 카페 menu.txt를 파싱해 DB에 저장."""
    conn = await asyncpg.connect(DB_DSN)
    try:
        total = 0
        for cafe_dir in sorted(OUTPUT_DIR.iterdir()):
            if not cafe_dir.is_dir():
                continue
            menu_file = cafe_dir / "texts" / "menu.txt"
            if not menu_file.exists():
                continue

            cafe_name = cafe_dir.name
            text = menu_file.read_text(encoding="utf-8")
            menus = parse_menu_txt(text)

            print(f"\n[{cafe_name}] {len(menus)}개 메뉴 파싱")
            for m in menus:
                price_str = f"{m['price']:,}원" if m["price"] is not None else "가격 없음"
                print(f"  - {m['name']}: {price_str}")

            inserted = await insert_menus(conn, cafe_name, menus)
            print(f"  → {inserted}행 저장 완료 (cafe_id: {cafe_uuid(cafe_name)})")
            total += inserted

        print(f"\n[완료] 총 {total}개 메뉴 저장")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(process_all_menus())
