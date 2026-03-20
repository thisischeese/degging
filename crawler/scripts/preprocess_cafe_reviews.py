from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ENRICHED = ROOT_DIR / "data" / "cafe_enriched.json"
DEFAULT_OUTPUT_ROOT = ROOT_DIR / "output"
DEFAULT_OUTPUT_JSON = ROOT_DIR / "data" / "cafe_reviews.json"

FOLLOW_MARKER = "팔로우"
MORE_MARKER = "더보기"
REACTION_MARKER = "반응 남기기"
TASTE_END_RE = re.compile(r".+가 맛있어요(?:\+\d+)?$")
NUMERIC_RE = re.compile(r"^\d+$")
MORE_REVIEW_RE = re.compile(r"^\d*개의 리뷰가 더 있습니다$")
VISIT_DATE_SHORT_RE = re.compile(r"^\d{1,2}\.\d{1,2}\.?(?:[월화수목금토일])?$")
VISIT_DATE_LONG_RE = re.compile(r"^\d{4}년 \d{1,2}월 \d{1,2}일 .+요일$")
VISIT_COUNT_RE = re.compile(r"^\d+번째 방문$")
REVIEW_STATS_RE = re.compile(r"^리뷰\s[\d,]+(?:사진\s[\d,]+)?(?:팔로워\s[\d,]+)?$")
VISIT_META_PREFIX_RE = re.compile(
    r"^(?:(?:동영상|다음|네이버 예약)\s*)*"
    r"(?:아침|점심|저녁|밤)에\s*방문"
    r".{0,40}?이용대기\s*시간\s*(?:바로\s*입장|\d+\s*분\s*이내)\s*"
)

REVIEW_UUID_NAMESPACE = uuid.UUID("c91d4b34-759f-4d95-bf1b-ec6f9d5d2c3b")
CONTEXT_PREFIX_RE = re.compile(
    r"^(?:일상|데이트|친목|나들이|기념일|비즈니스|가족모임)"
    r"(?:[\s,·・/]*(?:"
    r"일상|데이트|친목|나들이|기념일|비즈니스|가족모임|"
    r"혼자|친구|연인[·・]배우자|지인[·・]동료|친척[·・]형제자매|부모님|아이|반려동물|기타"
    r"))*"
)
LEADING_PUNCT_RE = re.compile(r"^[\s,.;:!~\-–—|]+")
NOISE_EXACT = {
    "개의 리뷰가 더 있습니다",
    "펼쳐보기",
    "접기",
    "방문일",
    "인증 수단",
    "영수증",
    "결제내역",
    "별점",
    "점",
    "명",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess review.txt files into cafe review JSON")
    parser.add_argument("--input-enriched", type=Path, default=DEFAULT_INPUT_ENRICHED)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    return parser.parse_args()


def normalize_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def load_cafe_ids(enriched_path: Path) -> list[str]:
    rows = json.loads(enriched_path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"Expected top-level JSON array: {enriched_path}")

    cafe_ids: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        cafe_id = row.get("cafe_id")
        if not cafe_id and isinstance(row.get("cafes"), dict):
            cafe_id = row["cafes"].get("cafe_id")
        if not isinstance(cafe_id, str):
            continue
        cafe_id = cafe_id.strip()
        if not cafe_id or cafe_id in seen:
            continue
        seen.add(cafe_id)
        cafe_ids.append(cafe_id)
    return cafe_ids


def find_end_index(lines: list[str], start: int) -> int:
    for idx in range(start, len(lines)):
        if lines[idx] == MORE_MARKER:
            return idx
    for idx in range(start, len(lines)):
        if TASTE_END_RE.fullmatch(lines[idx]):
            return idx

    for idx in range(start, len(lines)):
        if lines[idx] == REACTION_MARKER:
            return idx
    for idx in range(start, len(lines)):
        if lines[idx] == FOLLOW_MARKER:
            return idx
    return len(lines)


def strip_visit_meta_prefix(text: str) -> str:
    result = text.strip()
    while True:
        updated = VISIT_META_PREFIX_RE.sub("", result, count=1)
        if updated == result:
            break
        result = updated.strip()

    while True:
        context_removed = CONTEXT_PREFIX_RE.sub("", result, count=1)
        if context_removed == result:
            break
        result = context_removed.strip()

    result = LEADING_PUNCT_RE.sub("", result, count=1).strip()
    return result


def is_visit_meta_only_line(line: str) -> bool:
    if not line:
        return False
    return strip_visit_meta_prefix(line) == ""


def is_noise_line(line: str) -> bool:
    if not line:
        return True
    if line in NOISE_EXACT:
        return True
    if line in {FOLLOW_MARKER, MORE_MARKER, REACTION_MARKER}:
        return True
    if NUMERIC_RE.fullmatch(line):
        return True
    if MORE_REVIEW_RE.fullmatch(line):
        return True
    if VISIT_DATE_SHORT_RE.fullmatch(line):
        return True
    if VISIT_DATE_LONG_RE.fullmatch(line):
        return True
    if VISIT_COUNT_RE.fullmatch(line):
        return True
    if REVIEW_STATS_RE.fullmatch(line):
        return True
    if is_visit_meta_only_line(line):
        return True
    return False


def clean_review_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if not is_noise_line(line)]


def build_user_id(cafe_id: str, review_index: int, user_review: str) -> str:
    key = f"{cafe_id}:{review_index}:{user_review}"
    return str(uuid.uuid5(REVIEW_UUID_NAMESPACE, key))


def extract_cafe_reviews(cafe_id: str, lines: list[str]) -> list[dict[str, str]]:
    reviews: list[dict[str, str]] = []
    for idx, line in enumerate(lines):
        if line != FOLLOW_MARKER:
            continue
        start = idx + 1
        if start >= len(lines):
            continue

        end = find_end_index(lines, start)
        chunk = clean_review_lines(lines[start:end])
        user_review = " ".join(chunk).strip()
        user_review = strip_visit_meta_prefix(user_review)
        if not user_review:
            continue

        review_index = len(reviews)
        reviews.append(
            {
                "user_id": build_user_id(cafe_id, review_index, user_review),
                "user_review": user_review,
            }
        )
    return reviews


def preprocess_single_cafe(cafe_id: str, output_root: Path) -> list[dict[str, str]]:
    review_path = output_root / cafe_id / "texts" / "review.txt"
    if not review_path.exists():
        return []
    text = review_path.read_text(encoding="utf-8")
    lines = normalize_lines(text)
    return extract_cafe_reviews(cafe_id, lines)


def build_cafe_reviews_payload(enriched_path: Path, output_root: Path) -> list[dict[str, Any]]:
    cafe_ids = load_cafe_ids(enriched_path)
    payload: list[dict[str, Any]] = []
    for cafe_id in cafe_ids:
        payload.append(
            {
                "cafe_id": cafe_id,
                "cafe_reviews": preprocess_single_cafe(cafe_id, output_root),
            }
        )
    return payload


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    payload = build_cafe_reviews_payload(args.input_enriched, args.output_root)
    write_json(args.output_json, payload)

    total_reviews = sum(len(item["cafe_reviews"]) for item in payload)
    print(f"Cafes processed: {len(payload)}")
    print(f"Reviews extracted: {total_reviews}")
    print(f"Written: {args.output_json}")


if __name__ == "__main__":
    main()
