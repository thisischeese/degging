from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import re
import urllib.parse
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import TYPE_CHECKING, Any

from app.core.config import settings
from app.core.metrics import record_result, track_inflight, track_stage
from app.models.cafe_crawling import CafeCrawlingMergedItem, CafeCrawlingRequestItem, CafeCrawlingResponse
from app.services.cafe_crawling_service import (
    BLOCK_HOSTS,
    COMPANION_WORDS,
    DEFAULT_IMAGE_MAX_EDGE_PX,
    DEFAULT_UA,
    DEFAULT_VIBE_TAG_ID,
    GMS_CHAT_COMPLETIONS_URL,
    LABEL_TOKENS,
    MAX_PHOTOS,
    MAX_REVIEWS,
    NAVER_MAP_BASE_URL,
    PRESIGN_EXPIRES_SECONDS,
    PURPOSE_WORDS,
    SCROLL_STEP_PX,
    SCROLL_WAIT_SECONDS,
    SEARCH_FRAME_TIMEOUT_SECONDS,
    SEARCH_RESPONSE_TIMEOUT_SECONDS,
    SEARCH_URL_EXTRACTION_POLL_SECONDS,
    SETTLE_WAIT_SECONDS,
    S3UploadError,
    S3_KEY_PREFIX,
    TAB_CONFIG,
    TAB_READY_SELECTORS,
    TAB_SCROLL_STEPS,
    VIBE_TAGS,
    WINDOWS_PLAYWRIGHT_LOOP_ERROR,
    _BLOCK_SEARCH,
    _BLOCK_TAB,
    _VIEWPORT_POOL,
    CafeCrawlingItemError,
    CafeCrawlingSourceError,
    CafeSeed,
    RuntimeSettings,
    build_cafe_reviews,
    clip_text,
    ensure_playwright_runtime_supported,
    extract_review_card_payloads as base_extract_review_card_payloads,
    extract_json_object,
    is_allowed_image_url,
    normalize_request_item,
    parse_business_hours,
    parse_intro,
    parse_menu_text,
    parse_review_metrics,
    parse_structured_visitor_reviews,
    place_url_from_all_search,
    prepare_image_for_upload,
    random_ua,
    resolve_runtime_settings,
    THUMBNAIL_MAX_EDGE_PX,
)

if TYPE_CHECKING:
    import httpx
    from playwright.async_api import Browser, BrowserContext, Page, Playwright


logger = logging.getLogger("uvicorn.error")
MAX_STALE_SCROLL_ROUNDS = 2
BROWSER_RECYCLE_CAFE_THRESHOLD = 10
MENU_IMAGE_KEY_SEGMENT = "menus"
MENU_IMAGE_SOURCE_FIELD = "_menu_image_source_url"
_LABEL_TOKEN_CASEFOLDS = frozenset(token.casefold() for token in LABEL_TOKENS)
_RESOURCE_COUNTER_LOCK = Lock()
_RESOURCE_COUNTERS = defaultdict(
    int,
    {
        "active_contexts": 0,
        "active_pages": 0,
        "browser_launches": 0,
        "browser_recycles": 0,
    },
)


@dataclass
class CrawlRequestResources:
    playwright: Playwright
    http_client: httpx.AsyncClient
    gms_client: "GMSClient"
    s3_client: "S3Client"
    tab_concurrency: int
    image_concurrency: int


@dataclass
class OrderedCrawlResult:
    item: dict[str, Any] | None = None
    missing_cafe_id: str | None = None
    failed_cafe_id: str | None = None
    failure_reason: str | None = None


@dataclass
class WorkerBrowserState:
    worker_id: int
    browser: Browser | None = None
    browser_generation: int = 0
    cafes_processed_in_browser: int = 0
    needs_recycle: bool = False
    recycle_reason: str | None = None


@dataclass(frozen=True)
class MenuCardPayload:
    menu_name: str
    price: int | None = None
    menu_description: str | None = None
    image_url: str | None = None


def reset_resource_counters_for_test() -> None:
    with _RESOURCE_COUNTER_LOCK:
        for key in _RESOURCE_COUNTERS:
            _RESOURCE_COUNTERS[key] = 0


def get_resource_counters_snapshot() -> dict[str, int]:
    with _RESOURCE_COUNTER_LOCK:
        return dict(_RESOURCE_COUNTERS)


def _adjust_resource_counter(name: str, delta: int) -> int:
    with _RESOURCE_COUNTER_LOCK:
        _RESOURCE_COUNTERS[name] = max(0, _RESOURCE_COUNTERS[name] + delta)
        return _RESOURCE_COUNTERS[name]


def _current_browser_cafe_index(worker_state: WorkerBrowserState) -> int:
    return worker_state.cafes_processed_in_browser + 1


def _mark_worker_browser_for_recycle(worker_state: WorkerBrowserState, reason: str) -> None:
    worker_state.needs_recycle = True
    worker_state.recycle_reason = reason


def _log_resource_state(event: str, **details: Any) -> None:
    logger.info(
        "Cafe crawling resource state: event=%s details=%s counters=%s",
        event,
        details,
        get_resource_counters_snapshot(),
    )


class GMSClient:
    def __init__(self, api_key: str, http_client: httpx.AsyncClient) -> None:
        self.api_key = api_key
        self.http_client = http_client

    async def chat(self, messages: list[dict[str, str]], *, temperature: float = 0.2, max_tokens: int = 300) -> str:
        payload = {"model": "gpt-5-nano", "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        response = await self.http_client.post(GMS_CHAT_COMPLETIONS_URL, headers=headers, json=payload)
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

        developer_prompt = "Summarize the cafe introduction in 40 characters or fewer and return only the summary."
        user_prompt = f"Summarize this cafe introduction in 40 characters or fewer.\n\n{intro}"
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
            "Choose 1 to 3 vibe tags that best match the cafe reviews. "
            'Return JSON only in the form {"tag_ids": ["uuid1", "uuid2"]}.'
        )
        user_prompt = (
            "Available tags:\n"
            f"{tag_lines}\n\n"
            "Select 1 to 3 matching tag_ids from these reviews and return JSON only.\n"
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
    def __init__(self, runtime_settings: RuntimeSettings, http_client: httpx.AsyncClient) -> None:
        self.access_key = runtime_settings.s3_access_key
        self.secret_key = runtime_settings.s3_secret_key
        self.bucket = runtime_settings.s3_bucket_name
        self.region = runtime_settings.s3_region
        self.http_client = http_client

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
        response = await self.http_client.put(self.object_url(key), headers=headers, content=data)
        if response.status_code >= 400:
            raise S3UploadError(f"S3 upload failed with status {response.status_code}: {response.text[:200]}")
        return key


def tab_name_for_slug(slug: str) -> str:
    for tab_name, tab_slug in TAB_CONFIG.items():
        if tab_slug == slug:
            return tab_name
    raise KeyError(f"Unknown tab slug: {slug}")


def explain_crawl_exception(exc: Exception) -> Exception:
    message = str(exc)
    if isinstance(exc, NotImplementedError):
        return CafeCrawlingSourceError(WINDOWS_PLAYWRIGHT_LOOP_ERROR)
    if "Executable doesn't exist" in message or "playwright install" in message.lower():
        return CafeCrawlingSourceError(
            "Playwright Chromium browser is not installed. Run `playwright install chromium` in the ai environment."
        )
    return CafeCrawlingItemError(message)


@asynccontextmanager
async def open_crawl_request_resources(runtime_settings: RuntimeSettings):
    try:
        import httpx
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise CafeCrawlingSourceError(
            "playwright is required for /ai/cafes/crawling. Add it to the ai environment first."
        ) from exc

    ensure_playwright_runtime_supported()
    limits = httpx.Limits(
        max_connections=settings.cafe_http_max_connections,
        max_keepalive_connections=settings.cafe_http_max_connections,
    )
    timeout = httpx.Timeout(60.0)

    try:
        async with httpx.AsyncClient(timeout=timeout, limits=limits) as http_client:
            async with async_playwright() as playwright:
                yield CrawlRequestResources(
                    playwright=playwright,
                    http_client=http_client,
                    gms_client=GMSClient(runtime_settings.gms_api_key, http_client),
                    s3_client=S3Client(runtime_settings, http_client),
                    tab_concurrency=settings.cafe_tab_concurrency,
                    image_concurrency=settings.cafe_image_concurrency,
                )
    except CafeCrawlingSourceError:
        raise
    except Exception as exc:
        translated = explain_crawl_exception(exc)
        if isinstance(translated, CafeCrawlingSourceError):
            raise translated from exc
        raise


async def launch_worker_browser(resources: CrawlRequestResources, worker_state: WorkerBrowserState) -> Browser:
    try:
        browser = await resources.playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
    except Exception as exc:
        translated = explain_crawl_exception(exc)
        if isinstance(translated, CafeCrawlingSourceError):
            raise translated from exc
        raise CafeCrawlingSourceError(f"Failed to launch browser for worker {worker_state.worker_id}") from exc

    worker_state.browser = browser
    worker_state.browser_generation += 1
    worker_state.cafes_processed_in_browser = 0
    worker_state.needs_recycle = False
    worker_state.recycle_reason = None
    _adjust_resource_counter("browser_launches", 1)
    _log_resource_state(
        "browser_launch",
        worker_id=worker_state.worker_id,
        browser_generation=worker_state.browser_generation,
    )
    return browser


async def close_worker_browser(
    worker_state: WorkerBrowserState,
    *,
    reason: str,
    recycle: bool,
) -> None:
    browser = worker_state.browser
    if browser is None:
        worker_state.needs_recycle = False
        worker_state.recycle_reason = None
        worker_state.cafes_processed_in_browser = 0
        return

    if recycle:
        _adjust_resource_counter("browser_recycles", 1)

    try:
        await browser.close()
    except Exception as exc:
        logger.warning(
            "Cafe crawling browser close failed: worker_id=%s browser_generation=%s reason=%s message=%s counters=%s",
            worker_state.worker_id,
            worker_state.browser_generation,
            reason,
            str(exc),
            get_resource_counters_snapshot(),
        )
    finally:
        worker_state.browser = None
        worker_state.needs_recycle = False
        worker_state.recycle_reason = None
        worker_state.cafes_processed_in_browser = 0

    _log_resource_state(
        "browser_recycle" if recycle else "browser_close",
        worker_id=worker_state.worker_id,
        browser_generation=worker_state.browser_generation,
        reason=reason,
    )


async def ensure_worker_browser(resources: CrawlRequestResources, worker_state: WorkerBrowserState) -> Browser:
    if worker_state.browser is None:
        return await launch_worker_browser(resources, worker_state)
    return worker_state.browser


async def open_tracked_context(worker_state: WorkerBrowserState) -> BrowserContext:
    browser = worker_state.browser
    if browser is None:
        raise RuntimeError(f"Browser is not available for worker {worker_state.worker_id}")

    context = await browser.new_context(
        viewport=_VIEWPORT_POOL[0],
        user_agent=random_ua(),
        locale="ko-KR",
    )
    _adjust_resource_counter("active_contexts", 1)
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return context


async def close_tracked_context(
    context: BrowserContext,
    *,
    worker_state: WorkerBrowserState,
    seed: CafeSeed,
) -> None:
    try:
        await context.close()
    except Exception as exc:
        _mark_worker_browser_for_recycle(worker_state, "context_close_failure")
        logger.warning(
            "Cafe crawling context close failed: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s message=%s counters=%s",
            seed.cafe_id,
            seed.name,
            worker_state.worker_id,
            worker_state.browser_generation,
            _current_browser_cafe_index(worker_state),
            str(exc),
            get_resource_counters_snapshot(),
        )
    finally:
        _adjust_resource_counter("active_contexts", -1)


async def open_tracked_page(context: BrowserContext) -> Page:
    page = await context.new_page()
    _adjust_resource_counter("active_pages", 1)
    return page


async def close_tracked_page(
    page: Page,
    *,
    worker_state: WorkerBrowserState,
    seed: CafeSeed,
    page_scope: str,
) -> None:
    try:
        await page.close()
    except Exception as exc:
        _mark_worker_browser_for_recycle(worker_state, f"{page_scope}_page_close_failure")
        logger.warning(
            "Cafe crawling page close failed: cafe_id=%s name=%s page_scope=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s message=%s counters=%s",
            seed.cafe_id,
            seed.name,
            page_scope,
            worker_state.worker_id,
            worker_state.browser_generation,
            _current_browser_cafe_index(worker_state),
            str(exc),
            get_resource_counters_snapshot(),
        )
    finally:
        _adjust_resource_counter("active_pages", -1)


async def configure_page(page: Page, *, search_mode: bool = False) -> None:
    block_types = _BLOCK_SEARCH if search_mode else _BLOCK_TAB

    async def handle(route) -> None:
        request = route.request
        if any(host in request.url for host in BLOCK_HOSTS) or request.resource_type in block_types:
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", handle)


async def wait_for_page_ready(page: Page, *, ready_selectors: tuple[str, ...]) -> None:
    for selector in ready_selectors:
        try:
            await page.locator(selector).first.wait_for(state="attached", timeout=1500)
            break
        except Exception:
            continue

    with suppress(Exception):
        await page.wait_for_load_state("networkidle", timeout=int(SETTLE_WAIT_SECONDS * 1000))
    await asyncio.sleep(SETTLE_WAIT_SECONDS)


async def scroll_page(page: Page, *, max_rounds: int) -> None:
    stale_rounds = 0
    for _ in range(max_rounds):
        before = await page.evaluate("() => ({ top: window.scrollY, height: document.body.scrollHeight })")
        await page.evaluate(f"window.scrollBy(0, {SCROLL_STEP_PX})")
        with suppress(Exception):
            await page.wait_for_load_state("networkidle", timeout=int(SCROLL_WAIT_SECONDS * 1000))
        await asyncio.sleep(SCROLL_WAIT_SECONDS)
        after = await page.evaluate("() => ({ top: window.scrollY, height: document.body.scrollHeight })")
        if after["top"] <= before["top"] and after["height"] == before["height"]:
            stale_rounds += 1
            if stale_rounds >= MAX_STALE_SCROLL_ROUNDS:
                break
        else:
            stale_rounds = 0


async def extract_place_url(page: Page, timeout_sec: float = 20) -> str | None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_sec
    while loop.time() < deadline:
        for frame in page.frames:
            if "entryIframe" not in (frame.name or ""):
                continue
            match = re.search(r"(https://pcmap\.place\.naver\.com/[a-z]+/\d+)", frame.url)
            if match:
                return match.group(1)
        await asyncio.sleep(SEARCH_URL_EXTRACTION_POLL_SECONDS)
    return None


async def resolve_place_url(seed: CafeSeed, context: BrowserContext, *, worker_state: WorkerBrowserState) -> str:
    search_url = NAVER_MAP_BASE_URL + urllib.parse.quote(seed.name)
    search_page = await open_tracked_page(context)
    await configure_page(search_page, search_mode=True)
    all_search_data: dict[str, Any] = {}
    all_search_event = asyncio.Event()

    async def on_response(response) -> None:
        if "allSearch" not in response.url or "data" in all_search_data:
            return
        try:
            all_search_data["data"] = await response.json()
            all_search_event.set()
        except Exception:
            return

    search_page.on("response", on_response)
    place_base_url: str | None = None
    try:
        await search_page.goto(search_url, wait_until="commit", timeout=25000)
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(all_search_event.wait(), timeout=SEARCH_RESPONSE_TIMEOUT_SECONDS)

        if "data" in all_search_data:
            place_base_url = place_url_from_all_search(all_search_data["data"])
        if not place_base_url:
            place_base_url = await extract_place_url(search_page, timeout_sec=15)
        if not place_base_url:
            for frame in search_page.frames:
                if "searchIframe" not in (frame.name or ""):
                    continue
                loop = asyncio.get_running_loop()
                url_future: asyncio.Future[str] = loop.create_future()

                def on_frame_nav(nav_frame) -> None:
                    match = re.search(r"(https://pcmap\.place\.naver\.com/[a-z]+/\d+)", nav_frame.url or "")
                    if match and not url_future.done():
                        url_future.set_result(match.group(1))

                search_page.on("framenavigated", on_frame_nav)
                try:
                    await frame.locator("li a").first.click(timeout=8000)
                    place_base_url = await asyncio.wait_for(url_future, timeout=SEARCH_FRAME_TIMEOUT_SECONDS)
                except Exception:
                    place_base_url = None
                finally:
                    search_page.remove_listener("framenavigated", on_frame_nav)
                break
    finally:
        with suppress(Exception):
            search_page.remove_listener("response", on_response)
        await close_tracked_page(
            search_page,
            worker_state=worker_state,
            seed=seed,
            page_scope="search",
        )

    if not place_base_url:
        raise CafeCrawlingItemError(f"Failed to find a Naver Place entry for cafe_id={seed.cafe_id}")

    logger.info("Resolved place url: cafe_id=%s place_base_url=%s", seed.cafe_id, place_base_url)
    return place_base_url


async def fetch_tab_text(
    page: Page,
    tab_url: str,
    *,
    scroll_steps: int = 0,
    ready_selectors: tuple[str, ...] = ("body",),
) -> str:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=30000)
    await wait_for_page_ready(page, ready_selectors=ready_selectors)
    await scroll_page(page, max_rounds=scroll_steps)
    return (await page.evaluate("() => document.body.innerText")).strip()


def normalize_compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_optional_text(value: Any) -> str | None:
    text = normalize_compact_text(value)
    return text or None


def normalize_menu_name_key(value: Any) -> str:
    return normalize_compact_text(value).casefold()


def parse_menu_price_value(value: Any) -> int | None:
    text = normalize_compact_text(value).replace(" ", "").replace(",", "").replace("\uC6D0", "")
    if not text.isdigit():
        return None
    return int(text)


def normalize_image_source_url(url: Any) -> str | None:
    normalized = normalize_optional_text(url)
    if normalized is None:
        return None

    parsed = urllib.parse.urlparse(normalized)
    if (parsed.hostname or "").lower() == "search.pstatic.net":
        source_values = urllib.parse.parse_qs(parsed.query).get("src")
        if source_values:
            decoded_source = normalize_optional_text(source_values[0])
            if decoded_source:
                normalized = decoded_source

    if not is_allowed_image_url(normalized):
        return None

    high_quality = re.sub(r"/thumbnail/\d+x\d+(?:crop)?/", "/", normalized)
    return high_quality.split("?")[0]


def normalize_menu_card_payloads(raw_payloads: list[dict[str, Any]]) -> list[MenuCardPayload]:
    normalized_payloads: list[MenuCardPayload] = []
    seen: set[tuple[str, int | None, str | None, str | None]] = set()

    for raw_payload in raw_payloads:
        if not isinstance(raw_payload, dict):
            continue

        menu_name = normalize_optional_text(raw_payload.get("menu_name"))
        if menu_name is None or menu_name.casefold() in _LABEL_TOKEN_CASEFOLDS:
            continue

        payload = MenuCardPayload(
            menu_name=menu_name,
            price=parse_menu_price_value(raw_payload.get("price_text") or raw_payload.get("price")),
            menu_description=normalize_optional_text(raw_payload.get("menu_description")),
            image_url=normalize_image_source_url(raw_payload.get("image_url")),
        )
        signature = (
            normalize_menu_name_key(payload.menu_name),
            payload.price,
            payload.menu_description,
            payload.image_url,
        )
        if signature in seen:
            continue
        seen.add(signature)
        normalized_payloads.append(payload)

    return normalized_payloads


async def extract_menu_card_payloads(page: Page) -> list[MenuCardPayload]:
    raw_payloads = await page.evaluate(
        """
        (labelTokens) => {
            const normalize = (value) => (value || '').replace(/\\s+/g, ' ').trim();
            const isVisible = (element) => {
                if (!(element instanceof Element)) {
                    return false;
                }
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
            };
            const isPriceLine = (line) => /^[\\d,]+\\s*(?:\\uC6D0)?$/.test(line);
            const isLabel = (line) => labelTokens.includes(line.toLowerCase());
            const payloads = [];
            const structuredCards = Array.from(document.querySelectorAll('li.E2jtL'));
            for (const card of structuredCards) {
                if (!isVisible(card)) {
                    continue;
                }

                const menuName = normalize(card.querySelector('.lPzHi')?.textContent || '');
                const priceText = normalize(card.querySelector('.p2H02')?.textContent || '');
                const menuDescription = normalize(card.querySelector('.okI98')?.textContent || '') || null;
                const imageNode = card.querySelector('.place_thumb img[src]');
                if (!menuName || isLabel(menuName) || (!priceText && !imageNode)) {
                    continue;
                }

                payloads.push({
                    menu_name: menuName,
                    menu_description: menuDescription,
                    price_text: priceText || null,
                    image_url: normalize(imageNode?.currentSrc || imageNode?.src || '') || null,
                });
            }

            if (payloads.length === 0) {
                const elements = Array.from(document.querySelectorAll('li, article, section, div'));
                for (const element of elements) {
                    if (!isVisible(element)) {
                        continue;
                    }

                    const rawText = normalize(element.innerText || '');
                    if (!rawText || rawText.length > 160) {
                        continue;
                    }

                    const lines = rawText
                        .split('\\n')
                        .map(normalize)
                        .filter(Boolean);
                    if (lines.length === 0 || lines.length > 8) {
                        continue;
                    }

                    const imageNode = element.querySelector('img[src]');
                    const hasPrice = lines.some(isPriceLine);
                    if (!imageNode && !hasPrice) {
                        continue;
                    }

                    const candidateLines = lines.filter((line) => !isLabel(line));
                    if (candidateLines.length === 0) {
                        continue;
                    }

                    let menuName = null;
                    let menuDescription = null;
                    let priceText = null;

                    for (const line of candidateLines) {
                        if (isPriceLine(line)) {
                            priceText = priceText || line;
                            continue;
                        }
                        if (!menuName) {
                            menuName = line;
                            continue;
                        }
                        if (!menuDescription) {
                            menuDescription = line;
                        }
                    }

                    if (!menuName) {
                        continue;
                    }

                    payloads.push({
                        menu_name: menuName,
                        menu_description: menuDescription,
                        price_text: priceText,
                        image_url: normalize(imageNode?.currentSrc || imageNode?.src || '') || null,
                    });
                }
            }

            return payloads;
        }
        """,
        sorted(_LABEL_TOKEN_CASEFOLDS),
    )
    return normalize_menu_card_payloads(raw_payloads)


async def extract_review_card_payloads(page: Page) -> list[dict[str, Any]]:
    return await base_extract_review_card_payloads(page)


async def fetch_review_tab_data(page: Page, tab_url: str) -> tuple[str, list[dict[str, Any]]]:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=30000)
    await wait_for_page_ready(page, ready_selectors=TAB_READY_SELECTORS["review"])

    raw_reviews: list[dict[str, Any]] = []
    seen_signatures: set[str] = set()
    stale_rounds = 0

    while len(raw_reviews) < MAX_REVIEWS and stale_rounds < MAX_STALE_SCROLL_ROUNDS:
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

        if len(raw_reviews) >= MAX_REVIEWS or stale_rounds >= MAX_STALE_SCROLL_ROUNDS:
            break

        await page.evaluate(f"window.scrollBy(0, {SCROLL_STEP_PX + 100})")
        with suppress(Exception):
            await page.wait_for_load_state("networkidle", timeout=int(SCROLL_WAIT_SECONDS * 1000))
        await asyncio.sleep(SCROLL_WAIT_SECONDS)

    review_text = (await page.evaluate("() => document.body.innerText")).strip()
    parsed_reviews = parse_structured_visitor_reviews(raw_reviews)
    logger.info(
        "Fetched review tab data: raw_reviews=%s parsed_reviews=%s review_text_chars=%s",
        len(raw_reviews),
        len(parsed_reviews),
        len(review_text),
    )
    return review_text, parsed_reviews


async def collect_cdn_images(page: Page, *, scroll_steps: int = 0) -> list[str]:
    collected: set[str] = set()

    def on_request(request) -> None:
        normalized = normalize_image_source_url(request.url)
        if request.resource_type == "image" and normalized is not None:
            collected.add(normalized)

    page.on("request", on_request)
    try:
        if scroll_steps:
            await scroll_page(page, max_rounds=scroll_steps)

        srcs: list[str] = await page.evaluate(
            """
            () => Array.from(document.querySelectorAll('img[src]'))
                .map(img => img.src)
                .filter(src => src && !src.startsWith('data:'))
            """
        )
        for src in srcs:
            normalized = normalize_image_source_url(src)
            if normalized is not None:
                collected.add(normalized)
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


async def fetch_photo_tab_data(page: Page, tab_url: str) -> tuple[str, list[str]]:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=30000)
    await wait_for_page_ready(page, ready_selectors=TAB_READY_SELECTORS["photo"])
    await scroll_page(page, max_rounds=TAB_SCROLL_STEPS["photo"])
    photo_text = (await page.evaluate("() => document.body.innerText")).strip()
    photo_urls = collect_unique_urls(await collect_cdn_images(page))[:MAX_PHOTOS]
    return photo_text, photo_urls


async def fetch_menu_tab_data(page: Page, tab_url: str) -> tuple[str, list[MenuCardPayload]]:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=30000)
    await wait_for_page_ready(page, ready_selectors=TAB_READY_SELECTORS["menu"])
    await scroll_page(page, max_rounds=TAB_SCROLL_STEPS["menu"])
    menu_text = (await page.evaluate("() => document.body.innerText")).strip()
    menu_cards = await extract_menu_card_payloads(page)
    return menu_text, menu_cards


async def fetch_place_tabs(
    seed: CafeSeed,
    context: BrowserContext,
    place_base_url: str,
    *,
    tab_concurrency: int,
    worker_state: WorkerBrowserState,
) -> dict[str, Any]:
    texts: dict[str, str] = {}
    menu_cards: list[MenuCardPayload] = []
    photo_urls: list[str] = []
    visitor_reviews: list[dict[str, Any]] = []
    tab_semaphore = asyncio.Semaphore(tab_concurrency)

    async def fetch_single_tab(tab_name: str, slug: str) -> None:
        nonlocal menu_cards, photo_urls, visitor_reviews
        async with tab_semaphore:
            async with track_inflight("tab"):
                page = await open_tracked_page(context)
                try:
                    await configure_page(page, search_mode=False)
                    tab_url = f"{place_base_url}/{slug}"
                    if slug == "review":
                        texts[tab_name], visitor_reviews = await fetch_review_tab_data(page, tab_url)
                    elif slug == "menu":
                        texts[tab_name], menu_cards = await fetch_menu_tab_data(page, tab_url)
                    elif slug == "photo":
                        texts[tab_name], photo_urls = await fetch_photo_tab_data(page, tab_url)
                    else:
                        texts[tab_name] = await fetch_tab_text(
                            page,
                            tab_url,
                            scroll_steps=TAB_SCROLL_STEPS.get(slug, 0),
                            ready_selectors=TAB_READY_SELECTORS.get(slug, ("body",)),
                        )
                    logger.info(
                        "Fetched tab: cafe_id=%s tab=%s text_chars=%s menu_cards=%s photo_urls=%s visitor_reviews=%s",
                        seed.cafe_id,
                        tab_name,
                        len(texts[tab_name]),
                        len(menu_cards),
                        len(photo_urls),
                        len(visitor_reviews),
                    )
                finally:
                    await close_tracked_page(
                        page,
                        worker_state=worker_state,
                        seed=seed,
                        page_scope=slug,
                    )

    async with asyncio.TaskGroup() as task_group:
        for tab_name, slug in TAB_CONFIG.items():
            task_group.create_task(fetch_single_tab(tab_name, slug))

    return {
        "texts": texts,
        "menu_cards": menu_cards,
        "photo_urls": photo_urls,
        "visitor_reviews": visitor_reviews,
        "place_base_url": place_base_url,
    }


async def crawl_place(seed: CafeSeed, resources: CrawlRequestResources, worker_state: WorkerBrowserState) -> dict[str, Any]:
    context: BrowserContext | None = None
    try:
        context = await open_tracked_context(worker_state)
        with track_stage("resolve_place"):
            place_base_url = await resolve_place_url(seed, context, worker_state=worker_state)
        with track_stage("tabs"):
            return await fetch_place_tabs(
                seed,
                context,
                place_base_url,
                tab_concurrency=resources.tab_concurrency,
                worker_state=worker_state,
            )
    except CafeCrawlingItemError:
        logger.warning("crawl_place item error: cafe_id=%s name=%s", seed.cafe_id, seed.name)
        raise
    except Exception as exc:
        _mark_worker_browser_for_recycle(worker_state, "crawl_place_exception")
        translated = explain_crawl_exception(exc)
        logger.exception(
            "crawl_place unexpected failure: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s message=%s",
            seed.cafe_id,
            seed.name,
            worker_state.worker_id,
            worker_state.browser_generation,
            _current_browser_cafe_index(worker_state),
            str(exc),
        )
        if isinstance(translated, CafeCrawlingSourceError):
            raise translated from exc
        raise CafeCrawlingItemError(f"Failed to crawl cafe_id={seed.cafe_id}") from exc
    finally:
        if context is not None:
            await close_tracked_context(
                context,
                worker_state=worker_state,
                seed=seed,
            )


async def download_image_bytes(url: str, http_client: httpx.AsyncClient) -> tuple[bytes, str]:
    headers = {"User-Agent": DEFAULT_UA, "Referer": "https://pcmap.place.naver.com/"}
    response = await http_client.get(url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";")[0].strip() or "application/octet-stream"
    return response.content, content_type


def build_menus_with_image_candidates(menu_text: str, menu_cards: list[MenuCardPayload]) -> list[dict[str, Any]]:
    parsed_menus = parse_menu_text(menu_text)
    if not parsed_menus:
        return [
            {
                "menu_name": menu_card.menu_name,
                "price": menu_card.price,
                "menu_description": menu_card.menu_description,
                MENU_IMAGE_SOURCE_FIELD: menu_card.image_url,
            }
            for menu_card in menu_cards
        ]

    menu_card_queues: defaultdict[str, deque[MenuCardPayload]] = defaultdict(deque)
    for menu_card in menu_cards:
        name_key = normalize_menu_name_key(menu_card.menu_name)
        if name_key:
            menu_card_queues[name_key].append(menu_card)

    menus: list[dict[str, Any]] = []
    for parsed_menu in parsed_menus:
        name_key = normalize_menu_name_key(parsed_menu["menu_name"])
        matched_card = menu_card_queues[name_key].popleft() if name_key and menu_card_queues[name_key] else None
        menus.append(
            {
                "menu_name": parsed_menu["menu_name"],
                "price": parsed_menu["price"] if parsed_menu["price"] is not None else matched_card.price if matched_card else None,
                "menu_description": (
                    parsed_menu["menu_description"]
                    if parsed_menu["menu_description"] is not None
                    else matched_card.menu_description if matched_card else None
                ),
                MENU_IMAGE_SOURCE_FIELD: matched_card.image_url if matched_card else None,
            }
        )

    return menus


async def upload_menu_images(
    seed: CafeSeed,
    s3_client: S3Client,
    http_client: httpx.AsyncClient,
    menus: list[dict[str, Any]],
    *,
    max_concurrency: int,
) -> list[str | None]:
    stored_keys: list[str | None] = [None] * len(menus)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def upload_single(index: int, source_url: str) -> None:
        async with semaphore:
            try:
                data, content_type = await download_image_bytes(source_url, http_client)
                data, content_type, ext = prepare_image_for_upload(data, max_edge_px=DEFAULT_IMAGE_MAX_EDGE_PX)
                key = f"{S3_KEY_PREFIX}/{seed.cafe_id}/{MENU_IMAGE_KEY_SEGMENT}/{index:02d}{ext}"
                stored_keys[index] = await s3_client.upload_bytes(key, data, content_type=content_type)
            except Exception:
                logger.warning("Menu image upload failed: cafe_id=%s menu_index=%s", seed.cafe_id, index)

    async with asyncio.TaskGroup() as task_group:
        for index, menu in enumerate(menus):
            source_url = menu.get(MENU_IMAGE_SOURCE_FIELD)
            if source_url:
                task_group.create_task(upload_single(index, source_url))

    return stored_keys


def finalize_uploaded_menu_keys(menus: list[dict[str, Any]], stored_keys: list[str | None]) -> list[dict[str, Any]]:
    finalized_menus: list[dict[str, Any]] = []
    for index, menu in enumerate(menus):
        finalized_menus.append(
            {
                "menu_name": menu["menu_name"],
                "price": menu["price"],
                "menu_description": menu["menu_description"],
                "menu_img_url": stored_keys[index] if index < len(stored_keys) else None,
            }
        )
    return finalized_menus


async def upload_cafe_images(
    seed: CafeSeed,
    s3_client: S3Client,
    http_client: httpx.AsyncClient,
    photo_urls: list[str],
    *,
    max_concurrency: int,
) -> tuple[str | None, list[dict[str, Any]]]:
    stored_keys: list[str | None] = [None] * min(len(photo_urls), MAX_PHOTOS)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def upload_single(index: int, source_url: str) -> None:
        async with semaphore:
            try:
                data, content_type = await download_image_bytes(source_url, http_client)
                max_edge_px = THUMBNAIL_MAX_EDGE_PX if index == 0 else DEFAULT_IMAGE_MAX_EDGE_PX
                data, content_type, ext = prepare_image_for_upload(data, max_edge_px=max_edge_px)
                key = f"{S3_KEY_PREFIX}/{seed.cafe_id}/images/{index:02d}{ext}"
                stored_keys[index] = await s3_client.upload_bytes(key, data, content_type=content_type)
            except Exception:
                logger.warning("Cafe image upload failed: cafe_id=%s index=%s", seed.cafe_id, index)

    async with asyncio.TaskGroup() as task_group:
        for index, source_url in enumerate(photo_urls[:MAX_PHOTOS]):
            task_group.create_task(upload_single(index, source_url))

    thumbnail_url: str | None = None
    image_rows: list[dict[str, Any]] = []
    sort_order = 0
    for index, stored_key in enumerate(stored_keys):
        if stored_key is None:
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


async def resolve_gms_enrichment(
    *,
    intro: str,
    review_texts: list[str],
    gms_client: GMSClient,
    worker_state: WorkerBrowserState,
    seed: CafeSeed,
) -> tuple[str, list[str]]:
    logger.info(
        "Cafe crawling GMS start: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s intro_chars=%s review_texts=%s",
        seed.cafe_id,
        seed.name,
        worker_state.worker_id,
        worker_state.browser_generation,
        _current_browser_cafe_index(worker_state),
        len(intro),
        len(review_texts),
    )
    summarized_intro = intro
    vibe_tag_ids = [DEFAULT_VIBE_TAG_ID]

    with track_stage("gms"):
        intro_task = asyncio.create_task(gms_client.summarize_intro(intro)) if intro and len(intro) > 40 else None
        vibe_task = asyncio.create_task(gms_client.choose_vibe_tag_ids(review_texts)) if review_texts else None

        if intro_task and vibe_task:
            summarized_intro, vibe_tag_ids = await asyncio.gather(intro_task, vibe_task)
        elif intro_task:
            summarized_intro = await intro_task
        elif vibe_task:
            vibe_tag_ids = await vibe_task

    logger.info(
        "Cafe crawling GMS complete: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s summarized_intro_chars=%s vibe_tag_count=%s",
        seed.cafe_id,
        seed.name,
        worker_state.worker_id,
        worker_state.browser_generation,
        _current_browser_cafe_index(worker_state),
        len(summarized_intro),
        len(vibe_tag_ids),
    )
    return summarized_intro, vibe_tag_ids


async def upload_images_with_metrics(
    seed: CafeSeed,
    resources: CrawlRequestResources,
    photo_urls: list[str],
    worker_state: WorkerBrowserState,
) -> tuple[str | None, list[dict[str, Any]]]:
    logger.info(
        "Cafe crawling image upload start: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s source_photo_count=%s",
        seed.cafe_id,
        seed.name,
        worker_state.worker_id,
        worker_state.browser_generation,
        _current_browser_cafe_index(worker_state),
        len(photo_urls),
    )
    with track_stage("images"):
        thumbnail_url, cafe_images = await upload_cafe_images(
            seed,
            resources.s3_client,
            resources.http_client,
            photo_urls,
            max_concurrency=resources.image_concurrency,
        )
    logger.info(
        "Cafe crawling image upload complete: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s thumbnail_present=%s stored_image_count=%s",
        seed.cafe_id,
        seed.name,
        worker_state.worker_id,
        worker_state.browser_generation,
        _current_browser_cafe_index(worker_state),
        bool(thumbnail_url),
        len(cafe_images),
    )
    return thumbnail_url, cafe_images


async def upload_menu_images_with_metrics(
    seed: CafeSeed,
    resources: CrawlRequestResources,
    menus: list[dict[str, Any]],
    worker_state: WorkerBrowserState,
) -> list[dict[str, Any]]:
    source_count = sum(1 for menu in menus if menu.get(MENU_IMAGE_SOURCE_FIELD))
    logger.info(
        "Cafe crawling menu image upload start: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s menu_count=%s source_menu_image_count=%s",
        seed.cafe_id,
        seed.name,
        worker_state.worker_id,
        worker_state.browser_generation,
        _current_browser_cafe_index(worker_state),
        len(menus),
        source_count,
    )
    stored_keys = await upload_menu_images(
        seed,
        resources.s3_client,
        resources.http_client,
        menus,
        max_concurrency=resources.image_concurrency,
    )
    uploaded_count = sum(1 for stored_key in stored_keys if stored_key is not None)
    logger.info(
        "Cafe crawling menu image upload complete: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s stored_menu_image_count=%s",
        seed.cafe_id,
        seed.name,
        worker_state.worker_id,
        worker_state.browser_generation,
        _current_browser_cafe_index(worker_state),
        uploaded_count,
    )
    return finalize_uploaded_menu_keys(menus, stored_keys)


def assign_sequence_ids(items: list[dict[str, Any]]) -> list[CafeCrawlingMergedItem]:
    return [CafeCrawlingMergedItem.model_validate(item) for item in items]


async def crawl_single_cafe(
    seed: CafeSeed,
    resources: CrawlRequestResources,
    worker_state: WorkerBrowserState,
) -> dict[str, Any]:
    with track_stage("total"):
        crawl_result = await crawl_place(seed, resources, worker_state)
        texts = crawl_result["texts"]

        home_text = texts[tab_name_for_slug("home")]
        menu_text = texts[tab_name_for_slug("menu")]
        review_text = texts[tab_name_for_slug("review")]
        info_text = texts[tab_name_for_slug("information")]

        intro = parse_intro(info_text)
        review_metrics = parse_review_metrics(review_text, crawl_result.get("visitor_reviews"))
        business_hours = parse_business_hours(home_text, info_text)
        menus = build_menus_with_image_candidates(menu_text, crawl_result.get("menu_cards", []))

        review_texts = [review["review_text"] for review in review_metrics["reviews"] if review.get("review_text")]
        logger.info(
            "Cafe crawling gather setup: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s menu_cards=%s photo_urls=%s review_texts=%s intro_chars=%s",
            seed.cafe_id,
            seed.name,
            worker_state.worker_id,
            worker_state.browser_generation,
            _current_browser_cafe_index(worker_state),
            len(crawl_result.get("menu_cards", [])),
            len(crawl_result["photo_urls"]),
            len(review_texts),
            len(intro),
        )
        image_task = asyncio.create_task(upload_images_with_metrics(seed, resources, crawl_result["photo_urls"], worker_state))
        menu_image_task = asyncio.create_task(upload_menu_images_with_metrics(seed, resources, menus, worker_state))
        gms_task = asyncio.create_task(
            resolve_gms_enrichment(
                intro=intro,
                review_texts=review_texts,
                gms_client=resources.gms_client,
                worker_state=worker_state,
                seed=seed,
            )
        )
        logger.info(
            "Cafe crawling gather waiting: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s image_task_done=%s menu_image_task_done=%s gms_task_done=%s",
            seed.cafe_id,
            seed.name,
            worker_state.worker_id,
            worker_state.browser_generation,
            _current_browser_cafe_index(worker_state),
            image_task.done(),
            menu_image_task.done(),
            gms_task.done(),
        )
        (thumbnail_url, cafe_images), menus, (summarized_intro, vibe_tag_ids) = await asyncio.gather(
            image_task,
            menu_image_task,
            gms_task,
        )
        logger.info(
            "Cafe crawling gather complete: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s image_task_done=%s menu_image_task_done=%s gms_task_done=%s thumbnail_present=%s image_count=%s menu_image_count=%s summarized_intro_chars=%s vibe_tag_count=%s",
            seed.cafe_id,
            seed.name,
            worker_state.worker_id,
            worker_state.browser_generation,
            _current_browser_cafe_index(worker_state),
            image_task.done(),
            menu_image_task.done(),
            gms_task.done(),
            bool(thumbnail_url),
            len(cafe_images),
            sum(1 for menu in menus if menu.get("menu_img_url")),
            len(summarized_intro),
            len(vibe_tag_ids),
        )

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
        cafe_vibe_tags = [{"tag_id": tag_id} for tag_id in vibe_tag_ids]

        logger.info(
            "Cafe crawling item assembled before return: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s thumbnail_present=%s image_count=%s menu_count=%s review_count=%s vibe_tag_count=%s",
            seed.cafe_id,
            seed.name,
            worker_state.worker_id,
            worker_state.browser_generation,
            _current_browser_cafe_index(worker_state),
            bool(thumbnail_url),
            len(cafe_images),
            len(menus),
            len(review_metrics["reviews"]),
            len(cafe_vibe_tags),
        )
        result = {
            "cafe_id": seed.cafe_id,
            "cafes": cafes,
            "cafe_rating_stats": cafe_rating_stats,
            "cafe_images": cafe_images,
            "cafe_menus": menus,
            "cafe_business_hours": cafe_business_hours,
            "cafe_vibe_tags": cafe_vibe_tags,
            "cafe_reviews": build_cafe_reviews(seed, review_metrics["reviews"]),
        }
        logger.info(
            "Cafe crawling item return payload: cafe_id=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s type=%s keys=%s",
            seed.cafe_id,
            worker_state.worker_id,
            worker_state.browser_generation,
            _current_browser_cafe_index(worker_state),
            type(result).__name__,
            sorted(result.keys()),
        )
        return result


async def _crawl_batch_item(
    *,
    index: int,
    total: int,
    seed: CafeSeed,
    resources: CrawlRequestResources,
    worker_state: WorkerBrowserState,
    ordered_results: list[OrderedCrawlResult | None],
) -> None:
    logger.info(
        "Cafe crawling item start: [%d/%d] cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s",
        index + 1,
        total,
        seed.cafe_id,
        seed.name,
        worker_state.worker_id,
        worker_state.browser_generation,
        _current_browser_cafe_index(worker_state),
    )
    crawled: dict[str, Any] | None = None
    async with track_inflight("cafe"):
        try:
            crawled = await crawl_single_cafe(seed, resources, worker_state)
            logger.info(
                "Cafe crawling item await returned: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s type=%s is_none=%s keys=%s",
                seed.cafe_id,
                seed.name,
                worker_state.worker_id,
                worker_state.browser_generation,
                _current_browser_cafe_index(worker_state),
                type(crawled).__name__ if crawled is not None else "NoneType",
                crawled is None,
                sorted(crawled.keys()) if isinstance(crawled, dict) else None,
            )
        except CafeCrawlingItemError:
            record_result(scope="item", status="item_failure")
            logger.warning(
                "Cafe crawling item missing: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s",
                seed.cafe_id,
                seed.name,
                worker_state.worker_id,
                worker_state.browser_generation,
                _current_browser_cafe_index(worker_state),
            )
            ordered_results[index] = OrderedCrawlResult(missing_cafe_id=seed.cafe_id)
            return
        except CafeCrawlingSourceError:
            record_result(scope="item", status="source_failure")
            raise
        except asyncio.CancelledError:
            record_result(scope="item", status="cancelled")
            logger.warning(
                "Cafe crawling item cancelled: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s",
                seed.cafe_id,
                seed.name,
                worker_state.worker_id,
                worker_state.browser_generation,
                _current_browser_cafe_index(worker_state),
            )
            ordered_results[index] = OrderedCrawlResult(
                failed_cafe_id=seed.cafe_id,
                failure_reason="cancelled",
            )
            raise
        except Exception:
            _mark_worker_browser_for_recycle(worker_state, "unexpected_failure")
            record_result(scope="item", status="unexpected_failure")
            logger.exception(
                "Cafe crawling item unexpected failure: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s",
                seed.cafe_id,
                seed.name,
                worker_state.worker_id,
                worker_state.browser_generation,
                _current_browser_cafe_index(worker_state),
            )
            ordered_results[index] = OrderedCrawlResult(
                failed_cafe_id=seed.cafe_id,
                failure_reason="unexpected_failure",
            )
            return

    if crawled is None:
        _mark_worker_browser_for_recycle(worker_state, "empty_result")
        record_result(scope="item", status="empty_result")
        logger.error(
            "Cafe crawling item produced empty result: cafe_id=%s name=%s worker_id=%s browser_generation=%s cafes_processed_in_browser=%s",
            seed.cafe_id,
            seed.name,
            worker_state.worker_id,
            worker_state.browser_generation,
            _current_browser_cafe_index(worker_state),
        )
        ordered_results[index] = OrderedCrawlResult(
            failed_cafe_id=seed.cafe_id,
            failure_reason="empty_result",
        )
        return

    record_result(scope="item", status="success")
    ordered_results[index] = OrderedCrawlResult(item=crawled)


async def _crawl_batch_worker(
    *,
    worker_id: int,
    total: int,
    queue: asyncio.Queue[tuple[int, CafeSeed] | None],
    resources: CrawlRequestResources,
    ordered_results: list[OrderedCrawlResult | None],
) -> None:
    worker_state = WorkerBrowserState(worker_id=worker_id)
    try:
        while True:
            queued = await queue.get()
            if queued is None:
                return

            index, seed = queued
            try:
                await ensure_worker_browser(resources, worker_state)
                await _crawl_batch_item(
                    index=index,
                    total=total,
                    seed=seed,
                    resources=resources,
                    worker_state=worker_state,
                    ordered_results=ordered_results,
                )
            finally:
                if worker_state.browser is not None:
                    worker_state.cafes_processed_in_browser += 1
                    if worker_state.needs_recycle or worker_state.cafes_processed_in_browser >= BROWSER_RECYCLE_CAFE_THRESHOLD:
                        recycle_reason = worker_state.recycle_reason or "max_cafes_per_browser"
                        await close_worker_browser(worker_state, reason=recycle_reason, recycle=True)
    finally:
        await close_worker_browser(worker_state, reason="worker_shutdown", recycle=False)


async def crawl_cafes_batch(request_items: list[CafeCrawlingRequestItem]) -> CafeCrawlingResponse:
    logger.info("Cafe crawling batch start: requested=%s", len(request_items))
    if not request_items:
        record_result(scope="batch", status="success")
        return CafeCrawlingResponse(items=[], total=0, missing_cafe_ids=[])

    runtime_settings = resolve_runtime_settings()
    seeds = [normalize_request_item(item) for item in request_items]
    ordered_results: list[OrderedCrawlResult | None] = [None] * len(seeds)
    worker_count = max(1, min(settings.cafe_batch_concurrency, len(seeds)))
    logger.info(
        "Cafe crawling batch worker setup: requested=%s worker_count=%s recycle_threshold=%s",
        len(seeds),
        worker_count,
        BROWSER_RECYCLE_CAFE_THRESHOLD,
    )
    queue: asyncio.Queue[tuple[int, CafeSeed] | None] = asyncio.Queue()
    for index, seed in enumerate(seeds):
        queue.put_nowait((index, seed))
    for _ in range(worker_count):
        queue.put_nowait(None)

    async with track_inflight("batch"):
        try:
            async with open_crawl_request_resources(runtime_settings) as resources:
                try:
                    async with asyncio.TaskGroup() as task_group:
                        for worker_id in range(worker_count):
                            task_group.create_task(
                                _crawl_batch_worker(
                                    worker_id=worker_id + 1,
                                    total=len(seeds),
                                    queue=queue,
                                    resources=resources,
                                    ordered_results=ordered_results,
                                )
                            )
                except* CafeCrawlingSourceError as exc_group:
                    record_result(scope="batch", status="source_failure")
                    raise exc_group.exceptions[0]
                except* Exception as exc_group:
                    record_result(scope="batch", status="unexpected_failure")
                    raise exc_group.exceptions[0]
        except CafeCrawlingSourceError:
            raise

    unresolved_cafe_ids = [seed.cafe_id for seed, result in zip(seeds, ordered_results) if result is None]
    if unresolved_cafe_ids:
        logger.warning(
            "Cafe crawling unresolved results before aggregation: count=%s cafe_ids=%s",
            len(unresolved_cafe_ids),
            unresolved_cafe_ids,
        )

    raw_items: list[dict[str, Any]] = []
    missing_cafe_ids: list[str] = []
    failed_cafe_ids: list[str] = []
    failed_details: list[dict[str, str]] = []
    for seed, result in zip(seeds, ordered_results):
        if result is None:
            failed_cafe_ids.append(seed.cafe_id)
            failed_details.append({"cafe_id": seed.cafe_id, "reason": "unresolved_result"})
            continue
        if result.missing_cafe_id is not None:
            missing_cafe_ids.append(result.missing_cafe_id)
        elif result.item is not None:
            raw_items.append(result.item)
        else:
            failed_cafe_id = result.failed_cafe_id or seed.cafe_id
            failure_reason = result.failure_reason or "unknown_failure"
            failed_cafe_ids.append(failed_cafe_id)
            failed_details.append({"cafe_id": failed_cafe_id, "reason": failure_reason})

    items = assign_sequence_ids(raw_items)
    response = CafeCrawlingResponse(
        items=items,
        total=len(items),
        missing_cafe_ids=missing_cafe_ids,
    )
    if failed_cafe_ids:
        logger.warning("Cafe crawling failed items: count=%s details=%s", len(failed_cafe_ids), failed_details)

    accounted_count = response.total + len(response.missing_cafe_ids) + len(failed_cafe_ids)
    if accounted_count != len(request_items):
        logger.error(
            "Cafe crawling batch accounting mismatch: requested=%s succeeded=%s missing=%s failed=%s",
            len(request_items),
            response.total,
            len(response.missing_cafe_ids),
            len(failed_cafe_ids),
        )

    record_result(scope="batch", status="success")
    logger.info(
        "Cafe crawling batch complete: requested=%s succeeded=%s missing=%s failed=%s resource_counters=%s",
        len(request_items),
        response.total,
        len(response.missing_cafe_ids),
        len(failed_cafe_ids),
        get_resource_counters_snapshot(),
    )
    return response
