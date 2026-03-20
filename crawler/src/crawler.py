from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import mimetypes
import os
import random
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiofiles
import httpx

if TYPE_CHECKING:
    from playwright.async_api import Page


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
ENV_PATH = ROOT_DIR / ".env"
LOG_PATH = DATA_DIR / "batch_crawl_log.jsonl"
BLOCKED_PATH = DATA_DIR / "blocked_cafes.json"
DEFAULT_OUTPUT_PATH = DATA_DIR / "cafe_enriched.json"

NAVER_MAP_BASE_URL = "https://map.naver.com/p/search/"
GMS_CHAT_COMPLETIONS_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
S3_KEY_PREFIX = "cafes"
PRESIGN_EXPIRES_SECONDS = 604800
MAX_PHOTOS = 6
MAX_REVIEWS = 10
BLOCK_MARKER = "서비스 이용이 제한"

TAB_CONFIG = {
    "홈": ("home", "home.txt"),
    "메뉴": ("menu", "menu.txt"),
    "리뷰": ("review", "review.txt"),
    "사진": ("photo", "photo.txt"),
    "정보": ("information", "info.txt"),
}

REQUIRED_ENV_KEYS = (
    "S3_SECRET_KEY",
    "S3_ACCESS_KEY",
    "S3_BUCKET_NAME",
    "S3_REGION",
    "GMS_API_KEY",
)

_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]
DEFAULT_UA = _UA_POOL[0]

_VIEWPORT_POOL = [
    {"width": 1400, "height": 900},
    {"width": 1280, "height": 800},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1920, "height": 1080},
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

VIBE_TAGS = {
    "7ab663df-31be-43f8-b06a-2e8979806d89": "우드톤/따뜻함",
    "4ada6e46-3d5b-4ac8-abf9-9479abb35cfc": "식물원/플랜테리어",
    "c35facb1-f2ae-42aa-8234-522f6ae3352b": "힙한",
    "e747e844-db71-42ea-81cf-c25d510672b2": "조용한/차분한",
    "9b71769c-2293-4e06-bf37-f1fbf33c2853": "탁트인/뷰 좋은",
}
DEFAULT_VIBE_TAG_ID = "e747e844-db71-42ea-81cf-c25d510672b2"


@dataclass(frozen=True)
class Settings:
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


class S3UploadError(RuntimeError):
    """Raised when a signed S3 upload fails."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def random_ua() -> str:
    return random.choice(_UA_POOL)


def safe_name(name: str) -> str:
    name = name.replace("\n", " ").replace("\r", "").replace("\t", " ")
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def load_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, sep, value = stripped.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        env[key] = value
    return env


def load_settings(env_path: Path = ENV_PATH) -> Settings:
    env = load_dotenv(env_path)
    for key in REQUIRED_ENV_KEYS:
        if os.environ.get(key):
            env[key] = os.environ[key]

    missing = [key for key in REQUIRED_ENV_KEYS if not env.get(key)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return Settings(
        s3_secret_key=env["S3_SECRET_KEY"],
        s3_access_key=env["S3_ACCESS_KEY"],
        s3_bucket_name=env["S3_BUCKET_NAME"],
        s3_region=env["S3_REGION"],
        gms_api_key=env["GMS_API_KEY"],
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


def normalize_cafe_seed(entry: dict[str, Any]) -> CafeSeed:
    return CafeSeed(
        cafe_id=str(entry.get("cafeId") or entry.get("cafe_id") or "").strip(),
        bizes_id=str(entry.get("bizesId") or entry.get("bizes_id") or "").strip(),
        name=str(entry.get("name") or "").strip(),
        status=str(entry.get("status") or "OPEN").strip() or "OPEN",
        address=normalize_nullable_text(entry.get("address")),
        road_address=normalize_nullable_text(entry.get("roadAddress") or entry.get("road_address")),
        lon=coerce_float(entry.get("lon")),
        lat=coerce_float(entry.get("lat")),
        thumbnail_url=normalize_nullable_text(entry.get("thumbnailUrl") or entry.get("thumbnail_url")),
        kakao_place_id=normalize_nullable_text(entry.get("kakaoPlaceId") or entry.get("kakao_place_id")),
        kakao_map_url=normalize_nullable_text(entry.get("kakaoMapUrl") or entry.get("kakao_map_url")),
    )


def load_cafe_seeds(path: Path) -> list[CafeSeed]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}")
    seeds = [normalize_cafe_seed(item) for item in data if isinstance(item, dict)]
    invalid = [seed for seed in seeds if not seed.cafe_id or not seed.name]
    if invalid:
        raise ValueError("Every cafe row must include cafeId and name")
    return seeds


def build_cache_dirs(cafe_id: str) -> dict[str, Path]:
    base = OUTPUT_DIR / safe_name(cafe_id)
    return {"base": base, "texts": base / "texts", "meta": base / "meta"}


def ensure_dirs(paths: dict[str, Path]) -> None:
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)


def cache_complete(paths: dict[str, Path]) -> bool:
    required = [paths["texts"] / file_name for _, file_name in TAB_CONFIG.values()]
    required.extend([paths["meta"] / "photo_urls.json", paths["meta"] / "place.json"])
    if not all(path.exists() for path in required):
        return False
    home_text = (paths["texts"] / "home.txt").read_text(encoding="utf-8")
    return BLOCK_MARKER not in home_text


def load_cached_crawl(paths: dict[str, Path]) -> dict[str, Any]:
    texts = {
        tab_name: (paths["texts"] / file_name).read_text(encoding="utf-8")
        for tab_name, (_, file_name) in TAB_CONFIG.items()
    }
    photo_urls = json.loads((paths["meta"] / "photo_urls.json").read_text(encoding="utf-8"))
    place_base_url = json.loads((paths["meta"] / "place.json").read_text(encoding="utf-8"))["place_base_url"]
    return {"texts": texts, "photo_urls": photo_urls, "place_base_url": place_base_url, "cached": True}


async def save_crawl_cache(paths: dict[str, Path], result: dict[str, Any]) -> None:
    ensure_dirs(paths)
    for tab_name, (_, file_name) in TAB_CONFIG.items():
        async with aiofiles.open(paths["texts"] / file_name, "w", encoding="utf-8") as file:
            await file.write(result["texts"][tab_name])

    async with aiofiles.open(paths["meta"] / "photo_urls.json", "w", encoding="utf-8") as file:
        await file.write(json.dumps(result["photo_urls"], ensure_ascii=False, indent=2))

    async with aiofiles.open(paths["meta"] / "place.json", "w", encoding="utf-8") as file:
        await file.write(json.dumps({"place_base_url": result["place_base_url"]}, ensure_ascii=False, indent=2))


async def configure_page(page: Page, *, search_mode: bool = False) -> None:
    block_types = _BLOCK_SEARCH if search_mode else _BLOCK_TAB

    async def handle(route):
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


async def collect_cdn_images(page: Page, scroll_steps: int = 4) -> list[str]:
    collected: set[str] = set()

    def on_request(request):
        if request.resource_type == "image" and any(cdn in request.url for cdn in ["pstatic.net", "naver.net"]):
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
            if any(cdn in src for cdn in ["pstatic.net", "naver.net"]):
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


async def crawl_place(seed: CafeSeed, *, force: bool = False) -> dict[str, Any]:
    cache_dirs = build_cache_dirs(seed.cafe_id)
    if not force and cache_complete(cache_dirs):
        return load_cached_crawl(cache_dirs)

    search_url = NAVER_MAP_BASE_URL + urllib.parse.quote(seed.name)
    texts: dict[str, str] = {}
    photo_urls: list[str] = []
    place_base_url: str | None = None

    from playwright.async_api import async_playwright

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

        async def on_response(response):
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

                def on_frame_nav(nav_frame):
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
            raise RuntimeError("place base URL을 찾지 못했습니다. 검색 결과가 없거나 네이버 지도 구조가 변경되었을 수 있습니다.")

        tab_page = await context.new_page()
        await configure_page(tab_page, search_mode=False)

        for tab_name, (slug, _) in TAB_CONFIG.items():
            scroll_steps = 0
            if tab_name == "리뷰":
                scroll_steps = 6
            elif tab_name == "사진":
                scroll_steps = 4
            elif tab_name == "메뉴":
                scroll_steps = 2

            tab_url = f"{place_base_url}/{slug}"
            texts[tab_name] = await fetch_tab_text(tab_page, tab_url, scroll_steps=scroll_steps)
            if tab_name == "사진":
                photo_urls = collect_unique_urls(await collect_cdn_images(tab_page, scroll_steps=4))[:MAX_PHOTOS]
            await asyncio.sleep(random.uniform(1.5, 3.5))

        await tab_page.close()
        await browser.close()

    result = {"texts": texts, "photo_urls": photo_urls, "place_base_url": place_base_url, "cached": False}
    await save_crawl_cache(cache_dirs, result)
    return result


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
    start = skip_nav_header(lines)
    body = lines[start:]
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


def parse_phone(home_text: str) -> str | None:
    phone_re = re.compile(r"^(0\d{1,4}-\d{3,4}-\d{4})$")
    for line in read_lines(home_text):
        match = phone_re.match(line)
        if match:
            return match.group(1)
    return None


def parse_menu_text(menu_text: str) -> list[dict[str, Any]]:
    lines = read_lines(menu_text)
    start = skip_nav_header(lines)
    menus: list[dict[str, Any]] = []
    pending_name: str | None = None
    pending_desc: str | None = None

    body = lines[start:]
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


def parse_total_review_count(text: str) -> int:
    match = re.search(r"방문자 리뷰\s*([0-9,]+)", text)
    return int(match.group(1).replace(",", "")) if match else 0


def parse_rating_from_block(block: list[str]) -> int | None:
    for idx, line in enumerate(block):
        inline = re.search(r"별점\s*([1-5](?:\.\d+)?)", line)
        if inline:
            return int(round(float(inline.group(1))))
        point = re.search(r"([1-5](?:\.\d+)?)점", line)
        if point:
            return int(round(float(point.group(1))))
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


def parse_single_review(block: list[str]) -> dict[str, Any] | None:
    if len(block) < 4:
        return None

    result = {"rating": parse_rating_from_block(block), "review_text": None, "visit_purpose": None, "companion_type": None}
    result.update(parse_context(block[3]))

    reaction_idx: int | None = None
    for idx, line in enumerate(block):
        if line == "반응 남기기":
            reaction_idx = idx
            break

    end = reaction_idx if reaction_idx is not None else len(block)
    text_lines: list[str] = []
    for line in block[4:end]:
        if not line or line in {"더보기", "펼쳐보기", "반응 남기기", "팔로우", "방문일", "인증 수단"}:
            continue
        if re.match(r"^\d+$", line):
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


def parse_visitor_reviews(review_text: str) -> list[dict[str, Any]]:
    lines = read_lines(review_text)
    start = skip_nav_header(lines)
    body = lines[start:]
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
    return None if value is None else f"{value:.3f}"


def parse_ratio_from_summary(text: str, keywords: list[str]) -> float | None:
    for keyword in keywords:
        match = re.search(rf"{re.escape(keyword)}\s*([0-9]{{1,3}}(?:\.\d+)?)%", text)
        if not match:
            continue
        ratio = float(match.group(1))
        if 0 <= ratio <= 100:
            return ratio / 100
    return None


def parse_review_metrics(review_text: str) -> dict[str, Any]:
    total_review_count = parse_total_review_count(review_text)
    reviews = parse_visitor_reviews(review_text)[:MAX_REVIEWS]
    rating_sum = sum(review["rating"] or 0 for review in reviews)

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

    return {
        "review_count": total_review_count,
        "rating_sum": rating_sum,
        "solo_ratio": format_ratio(solo_ratio),
        "date_ratio": format_ratio(date_ratio),
        "friends_ratio": format_ratio(friends_ratio),
        "reviews": reviews,
    }


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
            if re.match(r"^(매주\s*)?([월화수목금토일](요일)?)(\s*[~,/-]\s*[월화수목금토일](요일)?)?", segment) and (
                re.search(r"\d{1,2}:\d{2}", segment) or "휴무" in segment
            ):
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

        specific_match = re.match(r"^([월화수목금토일](?:요일)?(?:\s*[~,/-]\s*[월화수목금토일](?:요일)?)?(?:\s*,\s*[월화수목금토일](?:요일)?)*)\s+(.+)$", clean)
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


def clip_text(text: str, limit: int = 40) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact if len(compact) <= limit else compact[:limit].rstrip()


class GMSClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.2, max_tokens: int = 300) -> str:
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
    def __init__(self, settings: Settings):
        self.access_key = settings.s3_access_key
        self.secret_key = settings.s3_secret_key
        self.bucket = settings.s3_bucket_name
        self.region = settings.s3_region

    @property
    def host(self) -> str:
        return f"{self.bucket}.s3.{self.region}.amazonaws.com"

    def object_url(self, key: str) -> str:
        return f"https://{self.host}/{urllib.parse.quote(key, safe='/~')}"

    async def upload_bytes(self, key: str, data: bytes, *, content_type: str = "application/octet-stream") -> str:
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
        return self.generate_presigned_url(key)

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
            f"{urllib.parse.quote(key, safe='')}={urllib.parse.quote(value, safe='~')}"
            for key, value in sorted(query_params.items())
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


async def download_image_bytes(url: str) -> tuple[bytes, str]:
    headers = {"User-Agent": DEFAULT_UA, "Referer": "https://pcmap.place.naver.com/"}
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").split(";")[0].strip() or "application/octet-stream"
        return response.content, content_type


def choose_extension(url: str, content_type: str) -> str:
    path = urllib.parse.urlparse(url).path
    ext = Path(path).suffix.lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        return ext
    guessed = mimetypes.guess_extension(content_type) or ".jpg"
    return ".jpg" if guessed == ".jpe" else guessed


async def upload_cafe_images(seed: CafeSeed, s3_client: S3Client, photo_urls: list[str], sequences: SequenceState) -> tuple[str | None, list[dict[str, Any]]]:
    thumbnail_url: str | None = None
    image_rows: list[dict[str, Any]] = []
    sort_order = 0

    for index, source_url in enumerate(photo_urls[:MAX_PHOTOS]):
        try:
            data, content_type = await download_image_bytes(source_url)
            ext = choose_extension(source_url, content_type)
            key = f"{S3_KEY_PREFIX}/{seed.cafe_id}/images/{index:02d}{ext}"
            presigned_url = await s3_client.upload_bytes(key, data, content_type=content_type)
        except Exception:
            continue

        if index == 0:
            thumbnail_url = presigned_url
            continue

        image_rows.append(
            {
                "image_id": sequences.next_image_id(),
                "image_url": presigned_url,
                "sort_order": sort_order,
                "cafe_id": seed.cafe_id,
            }
        )
        sort_order += 1

    return thumbnail_url, image_rows


def build_location(lon: float | None, lat: float | None) -> str | None:
    return None if lon is None or lat is None else f"SRID=4326;POINT({lon} {lat})"


async def enrich_cafe(seed: CafeSeed, settings: Settings, sequences: SequenceState, *, force: bool = False) -> dict[str, Any]:
    crawl_result = await crawl_place(seed, force=force)
    texts = crawl_result["texts"]

    gms_client = GMSClient(settings.gms_api_key)
    s3_client = S3Client(settings)

    intro = parse_intro(texts["정보"])
    summarized_intro = await gms_client.summarize_intro(intro) if intro and len(intro) > 40 else intro
    review_metrics = parse_review_metrics(texts["리뷰"])
    business_hours = parse_business_hours(texts["홈"], texts["정보"])

    menus: list[dict[str, Any]] = []
    for menu in parse_menu_text(texts["메뉴"]):
        menus.append(
            {
                "menu_id": sequences.next_menu_id(),
                "menu_name": menu["menu_name"],
                "price": menu["price"],
                "menu_description": menu["menu_description"],
                "cafe_id": seed.cafe_id,
            }
        )

    thumbnail_url, cafe_images = await upload_cafe_images(seed, s3_client, crawl_result["photo_urls"], sequences)

    review_texts = [review["review_text"] for review in review_metrics["reviews"] if review.get("review_text")]
    vibe_tag_ids = await gms_client.choose_vibe_tag_ids(review_texts)
    cafe_vibe_tags = [
        {
            "cafe_vibe_tag_id": sequences.next_cafe_vibe_tag_id(),
            "tag_id": tag_id,
            "cafe_id": seed.cafe_id,
        }
        for tag_id in vibe_tag_ids
    ]

    cafes = {
        "cafe_id": seed.cafe_id,
        "bizes_id": seed.bizes_id,
        "kakao_place_id": seed.kakao_place_id or "",
        "name": seed.name,
        "address": seed.address,
        "road_address": seed.road_address,
        "phone": parse_phone(texts["홈"]),
        "thumbnail_url": thumbnail_url,
        "status": seed.status or "OPEN",
        "location": build_location(seed.lon, seed.lat),
        "cafe_intro": summarized_intro or "",
        "franchise": False,
        "brandName": None,
        "branchName": None,
    }

    cafe_rating_stats = {
        "cafe_id": seed.cafe_id,
        "review_count": review_metrics["review_count"],
        "rating_sum": review_metrics["rating_sum"],
        "solo_ratio": review_metrics["solo_ratio"],
        "date_ratio": review_metrics["date_ratio"],
        "friends_ratio": review_metrics["friends_ratio"],
    }

    cafe_business_hours = {"cafe_id": seed.cafe_id, **business_hours}

    return {
        "cafe_id": seed.cafe_id,
        "cafes": cafes,
        "cafe_rating_stats": cafe_rating_stats,
        "cafe_images": cafe_images,
        "cafe_menus": menus,
        "cafe_business_hours": cafe_business_hours,
        "cafe_vibe_tags": cafe_vibe_tags,
    }


def append_log(entry: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


async def run_pipeline(input_path: Path, output_path: Path, *, offset: int = 0, limit: int | None = None, force: bool = False) -> list[dict[str, Any]]:
    settings = load_settings()
    seeds = load_cafe_seeds(input_path)
    targets = seeds[offset : offset + limit if limit is not None else None]
    results: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    sequences = SequenceState()

    for index, seed in enumerate(targets, start=1):
        started_at = datetime.now(timezone.utc)
        try:
            results.append(await enrich_cafe(seed, settings, sequences, force=force))
            append_log(
                {
                    "timestamp": utc_now_iso(),
                    "status": "ok",
                    "cafe_id": seed.cafe_id,
                    "name": seed.name,
                    "elapsed_sec": round((datetime.now(timezone.utc) - started_at).total_seconds(), 1),
                    "index": index,
                }
            )
        except Exception as exc:
            reason = str(exc)
            blocked.append({"cafe_id": seed.cafe_id, "name": seed.name, "reason": reason})
            append_log(
                {
                    "timestamp": utc_now_iso(),
                    "status": "fail",
                    "cafe_id": seed.cafe_id,
                    "name": seed.name,
                    "reason": reason,
                    "elapsed_sec": round((datetime.now(timezone.utc) - started_at).total_seconds(), 1),
                    "index": index,
                }
            )

    write_json(output_path, results)
    write_json(BLOCKED_PATH, blocked)
    return results


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Naver Place cafe enrichment pipeline")
    parser.add_argument("--input", type=Path, default=DATA_DIR / "cafe.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="Ignore cached crawl output")
    return parser


async def async_main(args: argparse.Namespace) -> None:
    await run_pipeline(args.input, args.output, offset=args.offset, limit=args.limit, force=args.force)


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
