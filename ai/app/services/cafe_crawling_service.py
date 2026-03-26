from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import random
import re
import sys
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import NAMESPACE_URL, uuid5

from PIL import Image, ImageOps

from app.core.config import settings
from app.models.cafe_crawling import (
    CafeCrawlingMergedItem,
    CafeCrawlingRequestItem,
    CafeCrawlingResponse,
)

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger("uvicorn.error")


NAVER_MAP_BASE_URL = "https://map.naver.com/p/search/"
GMS_CHAT_COMPLETIONS_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
S3_KEY_PREFIX = "cafes"
PRESIGN_EXPIRES_SECONDS = 604800
MAX_PHOTOS = 6
MAX_REVIEWS = 10
THUMBNAIL_MAX_EDGE_PX = 200
DEFAULT_IMAGE_MAX_EDGE_PX = 800
FALLBACK_IMAGE_MAX_EDGE_PX = 640
MAX_UPLOAD_IMAGE_BYTES = 512 * 1024
JPEG_QUALITY = 75
PNG_QUANTIZE_COLORS = 256
WINDOWS_PLAYWRIGHT_LOOP_ERROR = (
    "Playwright cannot launch Chromium under the current Windows asyncio event loop. "
    "The server is running a selector loop, which does not support subprocesses. "
    "Start Uvicorn without `--reload` or multiple workers on Windows, or move crawling "
    "to a separate process."
)

TAB_CONFIG = {
    "홈": "home",
    "메뉴": "menu",
    "리뷰": "review",
    "사진": "photo",
    "정보": "information",
}

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]
DEFAULT_UA = _UA_POOL[0]
_VIEWPORT_POOL = [
    {"width": 1400, "height": 900},
    {"width": 1280, "height": 800},
    {"width": 1440, "height": 900},
]
BLOCK_HOSTS = frozenset(
    {
        "mc.naver.com",
        "beagle.naver.com",
        "collect.veta.naver.com",
        "wcs.naver.com",
        "api.vworld.kr",
    }
)
ALLOWED_IMAGE_HOSTS = frozenset(
    {
        "pup-review-phinf.pstatic.net",
        "ldb-phinf.pstatic.net",
    }
)
_BLOCK_SEARCH = frozenset({"image", "font", "media", "stylesheet", "websocket", "other"})
_BLOCK_TAB = frozenset({"font", "media", "websocket", "other"})
NAV_TABS = {"홈", "메뉴", "리뷰", "사진", "정보"}
LABEL_TOKENS = {
    "대표",
    "best",
    "new",
    "인기",
    "추천",
    "품절",
    "준비중",
    "best seller",
    "BEST",
    "NEW",
    "사진",
}
MENU_STOP_PHRASES = ("메뉴 항목과 가격은", "메뉴판 이미지로 보기", "이용약관")
PRICE_RE = re.compile(r"^[\d,]+(원)?$")
REVIEWER_STATS_RE = re.compile(r"^리뷰\s+[\d,]+")
QUOTE_KW_RE = re.compile(r'^"(.+)"$')
KW_PLUS_RE = re.compile(r"^(.+?)\+(\d+)$")
KNOWN_KEYWORDS = {
    "빵이 맛있어요",
    "커피가 맛있어요",
    "매장이 청결해요",
    "인테리어가 멋져요",
    "특별한 메뉴가 있어요",
}
PURPOSE_WORDS = ["일상", "데이트", "친목", "비즈니스", "기념일"]
COMPANION_WORDS = [
    "혼자",
    "연인・배우자",
    "연인·배우자",
    "친구",
    "지인・동료",
    "지인·동료",
    "가족",
    "기타",
]
DAY_FIELD_MAP = {
    "월": "mon_hours",
    "화": "tues_hours",
    "수": "wed_hours",
    "목": "thur_hours",
    "금": "fri_hours",
    "토": "sat_hours",
    "일": "sun_hours",
}
DAY_ORDER = ["월", "화", "수", "목", "금", "토", "일"]
DAY_FIELDS = [DAY_FIELD_MAP[day] for day in DAY_ORDER]
TAB_SCROLL_STEPS = {"menu": 2, "photo": 4}
TAB_READY_SELECTORS = {
    "home": ("body",),
    "menu": ("li", "img[src]", "body"),
    "review": ("article", "li", "body"),
    "photo": ("img[src]", "body"),
    "information": ("body",),
}
SETTLE_WAIT_SECONDS = 0.5
SCROLL_WAIT_SECONDS = 0.35
SCROLL_STEP_PX = 800
SEARCH_RESPONSE_TIMEOUT_SECONDS = 8
SEARCH_FRAME_TIMEOUT_SECONDS = 10
SEARCH_URL_EXTRACTION_POLL_SECONDS = 0.5
MAX_STALE_SCROLL_ROUNDS = 2
VIBE_TAGS = {
    "7ab663df-31be-43f8-b06a-2e8979806d89": "우드톤/따뜻함",
    "4ada6e46-3d5b-4ac8-abf9-9479abb35cfc": "식물원/플랜테리어",
    "c35facb1-f2ae-42aa-8234-522f6ae3352b": "힙한",
    "e747e844-db71-42ea-81cf-c25d510672b2": "조용한/차분한",
    "9b71769c-2293-4e06-bf37-f1fbf33c2853": "탁트인/뷰 좋은",
}
DEFAULT_VIBE_TAG_ID = "e747e844-db71-42ea-81cf-c25d510672b2"


@dataclass(frozen=True)
class RuntimeSettings:
    s3_secret_key: str
    s3_access_key: str
    s3_bucket_name: str
    s3_region: str
    gms_api_key: str


@dataclass(frozen=True)
class CafeSeed:
    cafe_id: str
    bizes_id: str
    name: str
    status: str
    address: str | None
    road_address: str | None
    lon: float | None
    lat: float | None
    thumbnail_url: str | None
    kakao_place_id: str | None
    kakao_map_url: str | None


@dataclass
class SequenceState:
    image_id: int = 1
    menu_id: int = 1
    cafe_vibe_tag_id: int = 1

    def next_image_id(self) -> int:
        current = self.image_id
        self.image_id += 1
        return current

    def next_menu_id(self) -> int:
        current = self.menu_id
        self.menu_id += 1
        return current

    def next_cafe_vibe_tag_id(self) -> int:
        current = self.cafe_vibe_tag_id
        self.cafe_vibe_tag_id += 1
        return current


class CafeCrawlingSourceError(RuntimeError):
    """Raised when crawler prerequisites are missing or invalid."""


class CafeCrawlingItemError(RuntimeError):
    """Raised when a single cafe cannot be crawled."""


class S3UploadError(RuntimeError):
    """Raised when a signed S3 upload fails."""


def random_ua() -> str:
    return random.choice(_UA_POOL)


def resolve_runtime_settings() -> RuntimeSettings:
    values = {
        "S3_SECRET_KEY": settings.s3_secret_key,
        "S3_ACCESS_KEY": settings.s3_access_key,
        "S3_BUCKET_NAME": settings.s3_bucket_name,
        "S3_REGION": settings.s3_region,
        "GMS_API_KEY": settings.gms_api_key,
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise CafeCrawlingSourceError(
            f"Missing crawler runtime settings: {', '.join(missing)}"
        )

    return RuntimeSettings(
        s3_secret_key=values["S3_SECRET_KEY"],
        s3_access_key=values["S3_ACCESS_KEY"],
        s3_bucket_name=values["S3_BUCKET_NAME"],
        s3_region=values["S3_REGION"],
        gms_api_key=values["GMS_API_KEY"],
    )


def normalize_nullable_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def coerce_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_request_item(item: CafeCrawlingRequestItem) -> CafeSeed:
    return CafeSeed(
        cafe_id=item.cafeId,
        bizes_id="",
        name=item.name.strip(),
        status="OPEN",
        address=None,
        road_address=None,
        lon=None,
        lat=None,
        thumbnail_url=None,
        kakao_place_id=None,
        kakao_map_url=None,
    )


def read_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def skip_nav_header(lines: list[str]) -> int:
    found: set[str] = set()
    for idx, line in enumerate(lines):
        if line in NAV_TABS:
            found.add(line)
            if found == NAV_TABS:
                return idx + 1
    return 0


def parse_intro(info_text: str) -> str:
    lines = read_lines(info_text)
    body = lines[skip_nav_header(lines) :]
    desc_lines: list[str] = []
    in_desc = False
    for line in body:
        if line == "소개":
            in_desc = True
            continue
        if in_desc and line.startswith("편의시설"):
            break
        if in_desc:
            desc_lines.append(line)
    return " ".join(desc_lines).strip()


def parse_menu_text(menu_text: str) -> list[dict[str, Any]]:
    lines = read_lines(menu_text)
    body = lines[skip_nav_header(lines) :]
    menus: list[dict[str, Any]] = []
    pending_name: str | None = None
    pending_desc: str | None = None

    for index, line in enumerate(body):
        if any(line.startswith(stop) for stop in MENU_STOP_PHRASES):
            break
        if line.lower() in {token.lower() for token in LABEL_TOKENS}:
            continue
        if PRICE_RE.match(line):
            price = int(line.replace("원", "").replace(",", ""))
            if pending_name:
                menus.append({"menu_name": pending_name, "price": price, "menu_description": pending_desc})
                pending_name = None
                pending_desc = None
            continue
        if len(line) <= 30:
            next_line = body[index + 1] if index + 1 < len(body) else ""
            if pending_name and pending_desc is None and PRICE_RE.match(next_line):
                pending_desc = line
                continue
            if pending_name:
                menus.append({"menu_name": pending_name, "price": None, "menu_description": pending_desc})
            pending_name = line
            pending_desc = None
            continue
        pending_desc = line

    if pending_name:
        menus.append({"menu_name": pending_name, "price": None, "menu_description": pending_desc})
    return menus


def parse_total_review_count(visitor_reviews: list[dict[str, Any]] | int | None) -> int:
    if isinstance(visitor_reviews, int):
        count = visitor_reviews
    elif visitor_reviews is None:
        count = 0
    else:
        count = len(visitor_reviews)
    return max(0, min(count, MAX_REVIEWS))


def parse_rating_text(text: str) -> int | None:
    inline = re.search(r"(?:별점|평점)\s*([1-5](?:\.\d+)?)", text)
    if inline:
        return int(round(float(inline.group(1))))
    point = re.search(r"([1-5](?:\.\d+)?)\s*점", text)
    if point:
        return int(round(float(point.group(1))))
    return None


def parse_rating_from_block(block: list[str], *, rating_hint: int | None = None) -> int | None:
    if rating_hint is not None:
        return rating_hint
    for idx, line in enumerate(block):
        parsed = parse_rating_text(line)
        if parsed is not None:
            return parsed
        if line in {"별점", "평점"} and idx + 1 < len(block):
            next_line = block[idx + 1].strip()
            if re.fullmatch(r"[1-5](?:\.\d+)?", next_line):
                return int(round(float(next_line)))
    return None


def parse_context(line: str) -> dict[str, Any]:
    result = {"visit_purpose": None, "companion_type": None}
    for purpose in PURPOSE_WORDS:
        if purpose in line:
            result["visit_purpose"] = purpose
            break
    for companion in COMPANION_WORDS:
        if companion in line:
            result["companion_type"] = companion.replace("・", "·")
            break
    return result


def parse_context_from_lines(lines: list[str]) -> dict[str, Any]:
    result = {"visit_purpose": None, "companion_type": None}
    for line in lines:
        context = parse_context(line)
        if result["visit_purpose"] is None and context["visit_purpose"] is not None:
            result["visit_purpose"] = context["visit_purpose"]
        if result["companion_type"] is None and context["companion_type"] is not None:
            result["companion_type"] = context["companion_type"]
        if result["visit_purpose"] is not None and result["companion_type"] is not None:
            break
    return result


def is_review_context_line(line: str) -> bool:
    compact = re.sub(r"\s+", " ", line).strip()
    return (
        len(compact) <= 30
        and any(purpose in compact for purpose in PURPOSE_WORDS)
        and any(companion in compact for companion in COMPANION_WORDS)
    )


def is_review_metadata_line(line: str) -> bool:
    if line in {"더보기", "펼쳐보기", "반응 남기기", "팔로우", "방문일", "인증 수단"}:
        return True
    if REVIEWER_STATS_RE.match(line) or re.match(r"^\d+$", line):
        return True
    if line.startswith("방문일") or re.fullmatch(r"사진\s+\d+", line):
        return True
    if parse_rating_text(line) is not None or is_review_context_line(line):
        return True
    return False


def parse_single_review(block: list[str], *, rating_hint: int | None = None) -> dict[str, Any] | None:
    lines = [line.strip() for line in block if line and line.strip()]
    if not lines:
        return None

    result = {
        "reviewer_name": lines[0].strip() or None,
        "rating": parse_rating_from_block(lines, rating_hint=rating_hint),
        "review_text": None,
        "visit_purpose": None,
        "companion_type": None,
    }
    result.update(parse_context_from_lines(lines))

    reaction_idx: int | None = None
    for idx, line in enumerate(lines):
        if line == "반응 남기기":
            reaction_idx = idx
            break

    end = reaction_idx if reaction_idx is not None else len(lines)
    text_lines: list[str] = []
    for line in lines[1:end]:
        if not line or is_review_metadata_line(line):
            continue
        if line == "개의 리뷰가 더 있습니다":
            continue
        kw_plus = KW_PLUS_RE.match(line)
        if kw_plus and kw_plus.group(1) in KNOWN_KEYWORDS:
            continue
        if line in KNOWN_KEYWORDS or QUOTE_KW_RE.match(line):
            continue
        text_lines.append(line)

    result["review_text"] = " ".join(text_lines).strip() or None
    return result


def parse_structured_visitor_reviews(raw_reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for raw_review in raw_reviews:
        lines = raw_review.get("lines")
        if not isinstance(lines, list):
            continue
        block = [str(line).strip() for line in lines if str(line).strip()]
        if not block:
            continue
        rating_hint = parse_rating_text(str(raw_review.get("rating_text") or ""))
        parsed = parse_single_review(block, rating_hint=rating_hint)
        if parsed:
            reviews.append(parsed)
        if len(reviews) >= MAX_REVIEWS:
            break
    return reviews


def parse_visitor_reviews(review_text: str) -> list[dict[str, Any]]:
    lines = read_lines(review_text)
    body = lines[skip_nav_header(lines) :]
    review_start = 0
    for idx, line in enumerate(body):
        if "리뷰 클렌징" in line:
            review_start = idx + 1
            break
    review_body = body[review_start:]

    block_starts: list[int] = []
    for idx in range(1, len(review_body)):
        if REVIEWER_STATS_RE.match(review_body[idx]):
            block_starts.append(idx - 1)

    reviews: list[dict[str, Any]] = []
    for index, block_start in enumerate(block_starts):
        block_end = block_starts[index + 1] if index + 1 < len(block_starts) else len(review_body)
        parsed = parse_single_review(review_body[block_start:block_end])
        if parsed:
            reviews.append(parsed)
    return reviews


def format_ratio(value: float | None) -> str | None:
    if value is None:
        return None
    percentage = round(value * 100, 1)
    if float(percentage).is_integer():
        return f"{int(percentage)}%"
    return f"{percentage:.1f}%"


def parse_ratio_from_summary(text: str, keywords: list[str]) -> float | None:
    for keyword in keywords:
        match = re.search(rf"{re.escape(keyword)}\s*([0-9]{{1,3}}(?:\.\d+)?)%", text)
        if not match:
            continue
        ratio = float(match.group(1))
        if 0 <= ratio <= 100:
            return ratio / 100
    return None


def parse_review_metrics(review_text: str, visitor_reviews: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    reviews = (visitor_reviews or parse_visitor_reviews(review_text))[:MAX_REVIEWS]
    total_review_count = parse_total_review_count(reviews)
    rating_sum = total_review_count * 3

    joined = " ".join(read_lines(review_text))
    solo_ratio = parse_ratio_from_summary(joined, ["혼자"])
    date_ratio = parse_ratio_from_summary(joined, ["데이트", "연인·배우자", "연인・배우자"])
    friends_ratio = parse_ratio_from_summary(joined, ["친구"])

    if solo_ratio is None or date_ratio is None or friends_ratio is None:
        companions = [review["companion_type"] for review in reviews if review.get("companion_type")]
        if companions:
            total = len(companions)
            counts = {value: companions.count(value) for value in set(companions)}
            if solo_ratio is None:
                solo_ratio = counts.get("혼자", 0) / total
            if date_ratio is None:
                date_ratio = counts.get("연인·배우자", 0) / total
            if friends_ratio is None:
                friends_ratio = counts.get("친구", 0) / total

    metrics = {
        "review_count": total_review_count,
        "rating_sum": rating_sum,
        "solo_ratio": format_ratio(solo_ratio),
        "date_ratio": format_ratio(date_ratio),
        "friends_ratio": format_ratio(friends_ratio),
        "reviews": reviews,
    }
    logger.info(
        "Parsed review metrics: review_count=%s rating_sum=%s reviews=%s",
        metrics["review_count"],
        metrics["rating_sum"],
        len(metrics["reviews"]),
    )
    return metrics


def normalize_hours_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    return value.replace(" – ", " - ").replace(" ~ ", " - ")


def expand_day_expression(expr: str) -> list[str]:
    expr = expr.replace("요일", "").replace("매주", "").replace(" ", "")
    if not expr:
        return []
    if "," in expr:
        fields: list[str] = []
        for part in expr.split(","):
            fields.extend(expand_day_expression(part))
        return list(dict.fromkeys(fields))
    range_match = re.fullmatch(r"([월화수목금토일])[~-]([월화수목금토일])", expr)
    if range_match:
        start_idx = DAY_ORDER.index(range_match.group(1))
        end_idx = DAY_ORDER.index(range_match.group(2))
        if start_idx <= end_idx:
            return [DAY_FIELD_MAP[day] for day in DAY_ORDER[start_idx : end_idx + 1]]
        return [DAY_FIELD_MAP[day] for day in DAY_ORDER[start_idx:] + DAY_ORDER[: end_idx + 1]]
    return [DAY_FIELD_MAP[expr]] if expr in DAY_FIELD_MAP else []


def split_hour_segments(lines: list[str]) -> list[str]:
    segments: list[str] = []
    for raw_line in lines:
        line = re.sub(r"\s+", " ", raw_line.strip())
        if not line or line in NAV_TABS:
            continue
        for part in re.split(r"\s*/\s*", line):
            segment = part.strip()
            if not segment:
                continue
            if segment.startswith("영업시간"):
                segment = segment.replace("영업시간", "", 1).strip()
            if segment.startswith("오늘") or segment.startswith("접기") or segment.startswith("더보기"):
                continue
            if segment.startswith("라스트오더") or segment.startswith("브레이크타임") or segment.startswith("휴게시간"):
                continue
            if re.match(r"^(매일|평일|주말)\b", segment) and (re.search(r"\d{1,2}:\d{2}", segment) or "휴무" in segment):
                segments.append(segment)
                continue
            if re.match(
                r"^(매주\s*)?([월화수목금토일](요일)?)(\s*[~,/-]\s*[월화수목금토일](요일)?)?",
                segment,
            ) and (re.search(r"\d{1,2}:\d{2}", segment) or "휴무" in segment):
                segments.append(segment)
    return segments


def parse_business_hours_from_segments(segments: list[str]) -> dict[str, str | None]:
    result: dict[str, str | None] = {field: None for field in DAY_FIELDS}
    general_all: str | None = None
    weekdays: str | None = None
    weekends: str | None = None
    specifics: dict[str, str] = {}

    for segment in segments:
        clean = normalize_hours_value(segment).replace("매주 ", "")
        general_match = re.match(r"^(매일|평일|주말)\s+(.+)$", clean)
        if general_match:
            head, value = general_match.groups()
            if head == "매일":
                general_all = value
            elif head == "평일":
                weekdays = value
            else:
                weekends = value
            continue

        specific_match = re.match(
            r"^([월화수목금토일](?:요일)?(?:\s*[~,/-]\s*[월화수목금토일](?:요일)?)?(?:\s*,\s*[월화수목금토일](?:요일)?)*)\s+(.+)$",
            clean,
        )
        if not specific_match:
            continue
        expr, value = specific_match.groups()
        for field in expand_day_expression(expr):
            specifics[field] = value

    if general_all:
        for field in DAY_FIELDS:
            result[field] = general_all
    if weekdays:
        for day in DAY_ORDER[:5]:
            result[DAY_FIELD_MAP[day]] = weekdays
    if weekends:
        for day in DAY_ORDER[5:]:
            result[DAY_FIELD_MAP[day]] = weekends
    for field, value in specifics.items():
        result[field] = value
    return result


def parse_business_hours(home_text: str, info_text: str = "") -> dict[str, str | None]:
    return parse_business_hours_from_segments(split_hour_segments(read_lines(home_text) + read_lines(info_text)))


def extract_json_object(text: str) -> dict[str, Any] | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def clip_text(text: str, limit: int = 500) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact if len(compact) <= limit else compact[:limit].rstrip()


class GMSClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.2, max_tokens: int = 300) -> str:
        import httpx

        payload = {"model": "gpt-5-nano", "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(GMS_CHAT_COMPLETIONS_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
        return str(content)

    async def summarize_intro(self, intro: str) -> str:
        if not intro:
            return ""
        if len(intro) <= 40:
            return intro

        developer_prompt = "당신은 카페 소개를 40자 이하 한국어 한 줄로 요약한다. 설명 없이 평문만 반환한다."
        user_prompt = f"다음 카페 소개를 40자 이하로 요약해줘.\n\n{intro}"
        for _ in range(2):
            try:
                response = await self.chat(
                    [
                        {"role": "developer", "content": developer_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=120,
                )
                compact = clip_text(response, 40)
                if compact:
                    return compact
            except Exception:
                continue
        return clip_text(intro, 40)

    async def choose_vibe_tag_ids(self, reviews: list[str]) -> list[str]:
        if not reviews:
            return [DEFAULT_VIBE_TAG_ID]

        tag_lines = "\n".join(f"- {tag_id}: {tag_name}" for tag_id, tag_name in VIBE_TAGS.items())
        review_lines = "\n".join(f"{idx + 1}. {review}" for idx, review in enumerate(reviews[:MAX_REVIEWS]))
        developer_prompt = (
            "당신은 카페 리뷰를 읽고 가장 잘 맞는 분위기 태그를 고른다. "
            "반드시 JSON 객체만 반환하고 형식은 {\"tag_ids\": [\"uuid1\", \"uuid2\"]} 이다. "
            "태그는 최소 1개, 최대 3개만 고른다."
        )
        user_prompt = (
            "허용된 태그는 아래 5개뿐이야.\n"
            f"{tag_lines}\n\n"
            "리뷰를 읽고 가장 잘 맞는 tag_id를 1개에서 3개 고른 뒤 JSON으로만 답해줘.\n"
            f"{review_lines}"
        )

        for _ in range(2):
            try:
                response = await self.chat(
                    [
                        {"role": "developer", "content": developer_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=200,
                )
            except Exception:
                continue

            parsed = extract_json_object(response)
            if not parsed or not isinstance(parsed.get("tag_ids"), list):
                continue

            valid = [tag_id for tag_id in parsed["tag_ids"] if tag_id in VIBE_TAGS]
            valid = list(dict.fromkeys(valid))[:3]
            if valid:
                return valid

        return [DEFAULT_VIBE_TAG_ID]


def sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def get_signature_key(secret_key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
    key_date = sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    key_region = sign(key_date, region_name)
    key_service = sign(key_region, service_name)
    return sign(key_service, "aws4_request")


class S3Client:
    def __init__(self, runtime_settings: RuntimeSettings) -> None:
        self.access_key = runtime_settings.s3_access_key
        self.secret_key = runtime_settings.s3_secret_key
        self.bucket = runtime_settings.s3_bucket_name
        self.region = runtime_settings.s3_region

    @property
    def host(self) -> str:
        return f"{self.bucket}.s3.{self.region}.amazonaws.com"

    def object_url(self, key: str) -> str:
        return f"https://{self.host}/{urllib.parse.quote(key, safe='/~')}"

    async def upload_bytes(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
        import httpx

        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        canonical_uri = f"/{urllib.parse.quote(key, safe='/~')}"
        payload_hash = hashlib.sha256(data).hexdigest()
        canonical_headers = f"host:{self.host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
        signed_headers = "host;x-amz-content-sha256;x-amz-date"
        canonical_request = f"PUT\n{canonical_uri}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        credential_scope = f"{date_stamp}/{self.region}/s3/aws4_request"
        string_to_sign = (
            "AWS4-HMAC-SHA256\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )
        signing_key = get_signature_key(self.secret_key, date_stamp, self.region, "s3")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        authorization = (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )
        headers = {
            "Host": self.host,
            "Content-Type": content_type,
            "X-Amz-Content-Sha256": payload_hash,
            "X-Amz-Date": amz_date,
            "Authorization": authorization,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.put(self.object_url(key), headers=headers, content=data)
            if response.status_code >= 400:
                raise S3UploadError(f"S3 upload failed with status {response.status_code}: {response.text[:200]}")
        return key

    def generate_presigned_url(self, key: str, *, expires_in: int = PRESIGN_EXPIRES_SECONDS) -> str:
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        credential_scope = f"{date_stamp}/{self.region}/s3/aws4_request"
        canonical_uri = f"/{urllib.parse.quote(key, safe='/~')}"
        query_params = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{self.access_key}/{credential_scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires_in),
            "X-Amz-SignedHeaders": "host",
        }
        canonical_querystring = "&".join(
            f"{urllib.parse.quote(param_key, safe='')}={urllib.parse.quote(value, safe='~')}"
            for param_key, value in sorted(query_params.items())
        )
        canonical_headers = f"host:{self.host}\n"
        canonical_request = f"GET\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\nhost\nUNSIGNED-PAYLOAD"
        string_to_sign = (
            "AWS4-HMAC-SHA256\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )
        signing_key = get_signature_key(self.secret_key, date_stamp, self.region, "s3")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{self.object_url(key)}?{canonical_querystring}&X-Amz-Signature={signature}"


async def configure_page(page: Page, *, search_mode: bool = False) -> None:
    block_types = _BLOCK_SEARCH if search_mode else _BLOCK_TAB

    async def handle(route) -> None:
        request = route.request
        if any(host in request.url for host in BLOCK_HOSTS) or request.resource_type in block_types:
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", handle)


def place_url_from_all_search(data: dict[str, Any]) -> str | None:
    try:
        items = data["result"]["place"]["list"]
        if items:
            return f"https://pcmap.place.naver.com/restaurant/{items[0]['id']}"
    except (KeyError, TypeError, IndexError):
        return None
    return None


async def extract_place_url(page: Page, timeout_sec: int = 20) -> str | None:
    for _ in range(timeout_sec):
        for frame in page.frames:
            if "entryIframe" not in (frame.name or ""):
                continue
            match = re.search(r"(https://pcmap\.place\.naver\.com/[a-z]+/\d+)", frame.url)
            if match:
                return match.group(1)
        await asyncio.sleep(1)
    return None


async def fetch_tab_text(page: Page, tab_url: str, scroll_steps: int = 0) -> str:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(3)
    for _ in range(scroll_steps):
        await page.evaluate("window.scrollBy(0, 700)")
        await asyncio.sleep(0.8)
    return (await page.evaluate("() => document.body.innerText")).strip()


async def extract_review_card_payloads(page: Page) -> list[dict[str, Any]]:
    return await page.evaluate(
        """({ purposeWords, companionWords }) => {
            const normalize = (value) => value.replace(/\\s+/g, ' ').trim();
            const isVisible = (element) => {
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
            };
            const hasAny = (line, words) => words.some((word) => line.includes(word));
            const elements = Array.from(document.querySelectorAll('li, article, div'));
            const payloads = [];
            const seen = new Set();

            for (const element of elements) {
                if (!isVisible(element)) {
                    continue;
                }

                const rawText = (element.innerText || '').trim();
                if (!rawText) {
                    continue;
                }

                const lines = rawText
                    .split('\\n')
                    .map((line) => normalize(line))
                    .filter(Boolean);
                if (lines.length < 2 || lines.length > 40) {
                    continue;
                }

                const statsCount = lines.filter((line) => /^리뷰\\s+[\\d,]+/.test(line)).length;
                if (statsCount > 1) {
                    continue;
                }

                const ratingNode = element.querySelector('[aria-label*="별점"], [aria-label*="평점"]');
                const ratingText = normalize(ratingNode?.getAttribute('aria-label') || ratingNode?.textContent || '');
                const hasContextLine = lines.some(
                    (line) => hasAny(line, purposeWords) && hasAny(line, companionWords),
                );
                const hasReviewTextSignal = lines.some((line) => line.length >= 8);

                if (!hasReviewTextSignal) {
                    continue;
                }
                if (statsCount === 0 && !ratingText && !hasContextLine) {
                    continue;
                }

                const signature = JSON.stringify({ lines, ratingText });
                if (seen.has(signature)) {
                    continue;
                }
                seen.add(signature);
                payloads.push({ lines, rating_text: ratingText || null });
            }

            return payloads;
        }""",
        {"purposeWords": PURPOSE_WORDS, "companionWords": COMPANION_WORDS},
    )


async def fetch_review_tab_data(page: Page, tab_url: str) -> tuple[str, list[dict[str, Any]]]:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(3)

    raw_reviews: list[dict[str, Any]] = []
    seen_signatures: set[str] = set()
    stale_rounds = 0

    while len(raw_reviews) < MAX_REVIEWS and stale_rounds < 2:
        previous_count = len(raw_reviews)
        for payload in await extract_review_card_payloads(page):
            signature = json.dumps(payload, ensure_ascii=False, sort_keys=True)
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            raw_reviews.append(payload)
            if len(raw_reviews) >= MAX_REVIEWS:
                break

        if len(raw_reviews) == previous_count:
            stale_rounds += 1
        else:
            stale_rounds = 0

        if len(raw_reviews) >= MAX_REVIEWS or stale_rounds >= 2:
            break

        await page.evaluate("window.scrollBy(0, 900)")
        await asyncio.sleep(0.8)

    review_text = (await page.evaluate("() => document.body.innerText")).strip()
    parsed_reviews = parse_structured_visitor_reviews(raw_reviews)
    logger.info(
        "Fetched review tab data: raw_reviews=%s parsed_reviews=%s review_text_chars=%s",
        len(raw_reviews),
        len(parsed_reviews),
        len(review_text),
    )
    return review_text, parsed_reviews


def is_allowed_image_url(url: str) -> bool:
    host = urllib.parse.urlparse(url).hostname or ""
    return host.lower() in ALLOWED_IMAGE_HOSTS


async def collect_cdn_images(page: Page, scroll_steps: int = 4) -> list[str]:
    collected: set[str] = set()

    def on_request(request) -> None:
        if request.resource_type == "image" and is_allowed_image_url(request.url):
            collected.add(request.url.split("?")[0])

    page.on("request", on_request)
    try:
        for _ in range(scroll_steps):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(0.8)

        srcs: list[str] = await page.evaluate(
            """
            () => Array.from(document.querySelectorAll('img[src]'))
                .map(img => img.src)
                .filter(src => src && !src.startsWith('data:'))
            """
        )
        for src in srcs:
            if is_allowed_image_url(src):
                high_quality = re.sub(r"/thumbnail/\d+x\d+(?:crop)?/", "/", src)
                collected.add(high_quality.split("?")[0])
    finally:
        page.remove_listener("request", on_request)

    return [url for url in collected if not url.endswith((".svg", ".gif", ".ico"))]


def collect_unique_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        clean = url.split("?")[0]
        if clean in seen:
            continue
        seen.add(clean)
        result.append(clean)
    return result


def ensure_playwright_runtime_supported() -> None:
    if sys.platform != "win32":
        return

    loop_name = type(asyncio.get_running_loop()).__name__
    if "SelectorEventLoop" in loop_name:
        raise CafeCrawlingSourceError(
            f"{WINDOWS_PLAYWRIGHT_LOOP_ERROR} Current loop: {loop_name}."
        )


async def crawl_place(seed: CafeSeed) -> dict[str, Any]:
    logger.info("Starting crawl_place: cafe_id=%s name=%s", seed.cafe_id, seed.name)
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise CafeCrawlingSourceError(
            "playwright is required for /ai/cafes/crawling. Add it to the ai environment first."
        ) from exc

    ensure_playwright_runtime_supported()

    search_url = NAVER_MAP_BASE_URL + urllib.parse.quote(seed.name)
    texts: dict[str, str] = {}
    photo_urls: list[str] = []
    visitor_reviews: list[dict[str, Any]] = []
    place_base_url: str | None = None

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                viewport=random.choice(_VIEWPORT_POOL),
                user_agent=random_ua(),
                locale="ko-KR",
            )
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            search_page = await context.new_page()
            await configure_page(search_page, search_mode=True)
            all_search_data: dict[str, Any] = {}

            async def on_response(response) -> None:
                if "allSearch" in response.url and "data" not in all_search_data:
                    try:
                        all_search_data["data"] = await response.json()
                    except Exception:
                        return

            search_page.on("response", on_response)
            await search_page.goto(search_url, wait_until="commit", timeout=25000)

            for _ in range(8):
                if "data" in all_search_data:
                    break
                await asyncio.sleep(1)

            if "data" in all_search_data:
                place_base_url = place_url_from_all_search(all_search_data["data"])
            if not place_base_url:
                place_base_url = await extract_place_url(search_page, timeout_sec=15)
            if not place_base_url:
                for frame in search_page.frames:
                    if "searchIframe" not in (frame.name or ""):
                        continue
                    url_future: asyncio.Future[str] = asyncio.get_event_loop().create_future()

                    def on_frame_nav(nav_frame) -> None:
                        match = re.search(r"(https://pcmap\.place\.naver\.com/[a-z]+/\d+)", nav_frame.url or "")
                        if match and not url_future.done():
                            url_future.set_result(match.group(1))

                    search_page.on("framenavigated", on_frame_nav)
                    try:
                        await frame.locator("li a").first.click(timeout=8000)
                        place_base_url = await asyncio.wait_for(url_future, timeout=10)
                    except Exception:
                        place_base_url = None
                    finally:
                        search_page.remove_listener("framenavigated", on_frame_nav)
                    break

            await search_page.close()
            if not place_base_url:
                await browser.close()
                raise CafeCrawlingItemError(
                    f"Failed to find a Naver Place entry for cafe_id={seed.cafe_id}"
                )
            logger.info("Resolved place url: cafe_id=%s place_base_url=%s", seed.cafe_id, place_base_url)

            tab_page = await context.new_page()
            await configure_page(tab_page, search_mode=False)

            for tab_name, slug in TAB_CONFIG.items():
                if tab_name == "리뷰":
                    texts[tab_name], visitor_reviews = await fetch_review_tab_data(
                        tab_page,
                        f"{place_base_url}/{slug}",
                    )
                    logger.info(
                        "Fetched tab: cafe_id=%s tab=%s text_chars=%s visitor_reviews=%s",
                        seed.cafe_id,
                        tab_name,
                        len(texts[tab_name]),
                        len(visitor_reviews),
                    )
                else:
                    scroll_steps = 0
                    if tab_name == "사진":
                        scroll_steps = 4
                    elif tab_name == "메뉴":
                        scroll_steps = 2

                    tab_url = f"{place_base_url}/{slug}"
                    texts[tab_name] = await fetch_tab_text(tab_page, tab_url, scroll_steps=scroll_steps)
                    if tab_name == "사진":
                        photo_urls = collect_unique_urls(await collect_cdn_images(tab_page, scroll_steps=4))[:MAX_PHOTOS]
                    logger.info(
                        "Fetched tab: cafe_id=%s tab=%s text_chars=%s photo_urls=%s",
                        seed.cafe_id,
                        tab_name,
                        len(texts[tab_name]),
                        len(photo_urls),
                    )

                await asyncio.sleep(random.uniform(1.5, 3.5))

            await tab_page.close()
            await browser.close()
    except CafeCrawlingItemError:
        logger.warning("crawl_place item error: cafe_id=%s name=%s", seed.cafe_id, seed.name)
        raise
    except Exception as exc:
        message = str(exc)
        logger.exception("crawl_place unexpected failure: cafe_id=%s name=%s message=%s", seed.cafe_id, seed.name, message)
        if isinstance(exc, NotImplementedError):
            raise CafeCrawlingSourceError(WINDOWS_PLAYWRIGHT_LOOP_ERROR) from exc
        if "Executable doesn't exist" in message or "playwright install" in message.lower():
            raise CafeCrawlingSourceError(
                "Playwright Chromium browser is not installed. Run `playwright install chromium` in the ai environment."
            ) from exc
        raise CafeCrawlingItemError(f"Failed to crawl cafe_id={seed.cafe_id}") from exc

    return {
        "texts": texts,
        "photo_urls": photo_urls,
        "place_base_url": place_base_url,
        "visitor_reviews": visitor_reviews,
    }


async def download_image_bytes(url: str) -> tuple[bytes, str]:
    import httpx

    headers = {"User-Agent": DEFAULT_UA, "Referer": "https://pcmap.place.naver.com/"}
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";")[0].strip() or "application/octet-stream"
        return response.content, content_type


def _image_has_transparency(image: Image.Image) -> bool:
    if image.mode in {"RGBA", "LA"}:
        alpha = image.getchannel("A")
        extrema = alpha.getextrema()
        return extrema is not None and extrema[0] < 255

    if image.mode == "P":
        transparency = image.info.get("transparency")
        if transparency is None:
            return False
        if isinstance(transparency, bytes):
            return any(value < 255 for value in transparency)
        return True

    return False


def _resize_image_preserving_aspect(image: Image.Image, *, max_edge_px: int) -> Image.Image:
    width, height = image.size
    longest_edge = max(width, height)
    if longest_edge <= max_edge_px:
        return image.copy()

    scale = max_edge_px / longest_edge
    resized_size = (
        max(1, int(round(width * scale))),
        max(1, int(round(height * scale))),
    )
    return image.resize(resized_size, Image.Resampling.LANCZOS)


def _encode_image(image: Image.Image, *, has_transparency: bool) -> tuple[bytes, str, str]:
    output = BytesIO()
    if has_transparency:
        rgba_image = image.convert("RGBA")
        quantized_image = rgba_image.quantize(
            colors=PNG_QUANTIZE_COLORS,
            method=Image.Quantize.FASTOCTREE,
            dither=Image.Dither.NONE,
        )
        quantized_image.save(output, format="PNG", optimize=True, compress_level=9)
        return output.getvalue(), "image/png", ".png"

    rgb_image = image.convert("RGB")
    rgb_image.save(
        output,
        format="JPEG",
        quality=JPEG_QUALITY,
        optimize=True,
        progressive=True,
    )
    return output.getvalue(), "image/jpeg", ".jpg"


def prepare_image_for_upload(data: bytes, *, max_edge_px: int) -> tuple[bytes, str, str]:
    if max_edge_px <= 0:
        raise ValueError("max_edge_px must be positive")

    with Image.open(BytesIO(data)) as source_image:
        working_image = ImageOps.exif_transpose(source_image)
        if working_image is source_image:
            working_image = source_image.copy()

    has_transparency = _image_has_transparency(working_image)
    resized_image = _resize_image_preserving_aspect(working_image, max_edge_px=max_edge_px)
    encoded = _encode_image(resized_image, has_transparency=has_transparency)

    if max_edge_px > FALLBACK_IMAGE_MAX_EDGE_PX and len(encoded[0]) > MAX_UPLOAD_IMAGE_BYTES:
        fallback_image = _resize_image_preserving_aspect(working_image, max_edge_px=FALLBACK_IMAGE_MAX_EDGE_PX)
        encoded = _encode_image(fallback_image, has_transparency=has_transparency)

    return encoded


async def upload_cafe_images(
    seed: CafeSeed,
    s3_client: S3Client,
    photo_urls: list[str],
    sequences: SequenceState,
) -> tuple[str | None, list[dict[str, Any]]]:
    thumbnail_url: str | None = None
    image_rows: list[dict[str, Any]] = []
    sort_order = 0

    for index, source_url in enumerate(photo_urls[:MAX_PHOTOS]):
        try:
            data, content_type = await download_image_bytes(source_url)
            max_edge_px = THUMBNAIL_MAX_EDGE_PX if index == 0 else DEFAULT_IMAGE_MAX_EDGE_PX
            data, content_type, ext = prepare_image_for_upload(data, max_edge_px=max_edge_px)
            key = f"{S3_KEY_PREFIX}/{seed.cafe_id}/images/{index:02d}{ext}"
            stored_key = await s3_client.upload_bytes(key, data, content_type=content_type)
        except Exception:
            continue

        if index == 0:
            thumbnail_url = stored_key
            continue

        image_rows.append(
            {
                "image_url": stored_key,
                "sort_order": sort_order,
            }
        )
        sort_order += 1

    return thumbnail_url, image_rows


def build_cafe_reviews(seed: CafeSeed, reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cafe_reviews: list[dict[str, Any]] = []
    for index, review in enumerate(reviews):
        review_text = review.get("review_text")
        if not review_text:
            continue
        reviewer_name = review.get("reviewer_name") or "anonymous"
        review_identity = f"{seed.cafe_id}:{reviewer_name}:{index}:{review_text}"
        cafe_reviews.append(
            {
                "user_id": str(uuid5(NAMESPACE_URL, review_identity)),
                "user_review": review_text,
                "rating": 3,
            }
        )
    return cafe_reviews


async def enrich_cafe(seed: CafeSeed, runtime_settings: RuntimeSettings, sequences: SequenceState) -> dict[str, Any]:
    crawl_result = await crawl_place(seed)
    texts = crawl_result["texts"]

    gms_client = GMSClient(runtime_settings.gms_api_key)
    s3_client = S3Client(runtime_settings)

    intro = parse_intro(texts["정보"])
    summarized_intro = await gms_client.summarize_intro(intro) if intro and len(intro) > 500 else intro
    review_metrics = parse_review_metrics(texts["리뷰"], crawl_result.get("visitor_reviews"))
    business_hours = parse_business_hours(texts["홈"], texts["정보"])

    menus: list[dict[str, Any]] = []
    for menu in parse_menu_text(texts["메뉴"]):
        menus.append(
            {
                "menu_name": menu["menu_name"],
                "price": menu["price"],
                "menu_description": menu["menu_description"],
            }
        )

    thumbnail_url, cafe_images = await upload_cafe_images(seed, s3_client, crawl_result["photo_urls"], sequences)

    review_texts = [review["review_text"] for review in review_metrics["reviews"] if review.get("review_text")]
    vibe_tag_ids = await gms_client.choose_vibe_tag_ids(review_texts)
    cafe_vibe_tags = [
        {
            "tag_id": tag_id,
        }
        for tag_id in vibe_tag_ids
    ]

    cafes = {
        "cafe_id": seed.cafe_id,
        "name": seed.name,
        "thumbnail_url": thumbnail_url,
        "cafe_intro": summarized_intro or "",
    }

    cafe_rating_stats = {
        "review_count": review_metrics["review_count"],
        "rating_sum": review_metrics["rating_sum"],
        "solo_ratio": review_metrics["solo_ratio"],
        "date_ratio": review_metrics["date_ratio"],
        "friends_ratio": review_metrics["friends_ratio"],
    }

    cafe_business_hours = {**business_hours}

    return {
        "cafe_id": seed.cafe_id,
        "cafes": cafes,
        "cafe_rating_stats": cafe_rating_stats,
        "cafe_images": cafe_images,
        "cafe_menus": menus,
        "cafe_business_hours": cafe_business_hours,
        "cafe_vibe_tags": cafe_vibe_tags,
        "cafe_reviews": build_cafe_reviews(seed, review_metrics["reviews"]),
    }


class CafeCrawlingService:
    async def crawl_cafes(self, request_items: list[CafeCrawlingRequestItem]) -> CafeCrawlingResponse:
        from app.services.cafe_crawling_runtime import crawl_cafes_batch

        return await crawl_cafes_batch(request_items)

    async def crawl_single_cafe(
        self,
        seed: CafeSeed,
        resources: Any,
    ) -> dict[str, Any]:
        from app.services.cafe_crawling_runtime import crawl_single_cafe

        return await crawl_single_cafe(seed, resources)
