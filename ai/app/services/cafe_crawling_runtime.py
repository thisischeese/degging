from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import re
import urllib.parse
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timezone
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
    from playwright.async_api import Browser, BrowserContext, Page


logger = logging.getLogger("uvicorn.error")
MAX_STALE_SCROLL_ROUNDS = 2


@dataclass
class CrawlRequestResources:
    browser: Browser
    http_client: httpx.AsyncClient
    gms_client: "GMSClient"
    s3_client: "S3Client"
    batch_semaphore: asyncio.Semaphore
    tab_concurrency: int
    image_concurrency: int


@dataclass
class OrderedCrawlResult:
    item: dict[str, Any] | None = None
    missing_cafe_id: str | None = None


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
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                )
                try:
                    yield CrawlRequestResources(
                        browser=browser,
                        http_client=http_client,
                        gms_client=GMSClient(runtime_settings.gms_api_key, http_client),
                        s3_client=S3Client(runtime_settings, http_client),
                        batch_semaphore=asyncio.Semaphore(settings.cafe_batch_concurrency),
                        tab_concurrency=settings.cafe_tab_concurrency,
                        image_concurrency=settings.cafe_image_concurrency,
                    )
                finally:
                    await browser.close()
    except CafeCrawlingSourceError:
        raise
    except Exception as exc:
        translated = explain_crawl_exception(exc)
        if isinstance(translated, CafeCrawlingSourceError):
            raise translated from exc
        raise


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


async def resolve_place_url(seed: CafeSeed, context: BrowserContext) -> str:
    search_url = NAVER_MAP_BASE_URL + urllib.parse.quote(seed.name)
    search_page = await context.new_page()
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
        await search_page.close()

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
        if request.resource_type == "image" and is_allowed_image_url(request.url):
            collected.add(request.url.split("?")[0])

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


async def fetch_photo_tab_data(page: Page, tab_url: str) -> tuple[str, list[str]]:
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=30000)
    await wait_for_page_ready(page, ready_selectors=TAB_READY_SELECTORS["photo"])
    await scroll_page(page, max_rounds=TAB_SCROLL_STEPS["photo"])
    photo_text = (await page.evaluate("() => document.body.innerText")).strip()
    photo_urls = collect_unique_urls(await collect_cdn_images(page))[:MAX_PHOTOS]
    return photo_text, photo_urls


async def fetch_place_tabs(
    seed: CafeSeed,
    context: BrowserContext,
    place_base_url: str,
    *,
    tab_concurrency: int,
) -> dict[str, Any]:
    texts: dict[str, str] = {}
    photo_urls: list[str] = []
    visitor_reviews: list[dict[str, Any]] = []
    tab_semaphore = asyncio.Semaphore(tab_concurrency)

    async def fetch_single_tab(tab_name: str, slug: str) -> None:
        nonlocal photo_urls, visitor_reviews
        async with tab_semaphore:
            async with track_inflight("tab"):
                page = await context.new_page()
                try:
                    await configure_page(page, search_mode=False)
                    tab_url = f"{place_base_url}/{slug}"
                    if slug == "review":
                        texts[tab_name], visitor_reviews = await fetch_review_tab_data(page, tab_url)
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
                        "Fetched tab: cafe_id=%s tab=%s text_chars=%s photo_urls=%s visitor_reviews=%s",
                        seed.cafe_id,
                        tab_name,
                        len(texts[tab_name]),
                        len(photo_urls),
                        len(visitor_reviews),
                    )
                finally:
                    await page.close()

    async with asyncio.TaskGroup() as task_group:
        for tab_name, slug in TAB_CONFIG.items():
            task_group.create_task(fetch_single_tab(tab_name, slug))

    return {
        "texts": texts,
        "photo_urls": photo_urls,
        "visitor_reviews": visitor_reviews,
        "place_base_url": place_base_url,
    }


async def new_browser_context(browser: Browser) -> BrowserContext:
    context = await browser.new_context(
        viewport=_VIEWPORT_POOL[0],
        user_agent=random_ua(),
        locale="ko-KR",
    )
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return context


async def crawl_place(seed: CafeSeed, resources: CrawlRequestResources) -> dict[str, Any]:
    context: BrowserContext | None = None
    try:
        context = await new_browser_context(resources.browser)
        with track_stage("resolve_place"):
            place_base_url = await resolve_place_url(seed, context)
        with track_stage("tabs"):
            return await fetch_place_tabs(seed, context, place_base_url, tab_concurrency=resources.tab_concurrency)
    except CafeCrawlingItemError:
        logger.warning("crawl_place item error: cafe_id=%s name=%s", seed.cafe_id, seed.name)
        raise
    except Exception as exc:
        translated = explain_crawl_exception(exc)
        logger.exception(
            "crawl_place unexpected failure: cafe_id=%s name=%s message=%s",
            seed.cafe_id,
            seed.name,
            str(exc),
        )
        if isinstance(translated, CafeCrawlingSourceError):
            raise translated from exc
        raise CafeCrawlingItemError(f"Failed to crawl cafe_id={seed.cafe_id}") from exc
    finally:
        if context is not None:
            await context.close()


async def download_image_bytes(url: str, http_client: httpx.AsyncClient) -> tuple[bytes, str]:
    headers = {"User-Agent": DEFAULT_UA, "Referer": "https://pcmap.place.naver.com/"}
    response = await http_client.get(url, headers=headers, follow_redirects=True)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").split(";")[0].strip() or "application/octet-stream"
    return response.content, content_type


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
) -> tuple[str, list[str]]:
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

    return summarized_intro, vibe_tag_ids


async def upload_images_with_metrics(
    seed: CafeSeed,
    resources: CrawlRequestResources,
    photo_urls: list[str],
) -> tuple[str | None, list[dict[str, Any]]]:
    with track_stage("images"):
        return await upload_cafe_images(
            seed,
            resources.s3_client,
            resources.http_client,
            photo_urls,
            max_concurrency=resources.image_concurrency,
        )


def assign_sequence_ids(items: list[dict[str, Any]]) -> list[CafeCrawlingMergedItem]:
    return [CafeCrawlingMergedItem.model_validate(item) for item in items]


async def crawl_single_cafe(seed: CafeSeed, resources: CrawlRequestResources) -> dict[str, Any]:
    with track_stage("total"):
        crawl_result = await crawl_place(seed, resources)
        texts = crawl_result["texts"]

        home_text = texts[tab_name_for_slug("home")]
        menu_text = texts[tab_name_for_slug("menu")]
        review_text = texts[tab_name_for_slug("review")]
        info_text = texts[tab_name_for_slug("information")]

        intro = parse_intro(info_text)
        review_metrics = parse_review_metrics(review_text, crawl_result.get("visitor_reviews"))
        business_hours = parse_business_hours(home_text, info_text)
        menus = [
            {
                "menu_name": menu["menu_name"],
                "price": menu["price"],
                "menu_description": menu["menu_description"],
            }
            for menu in parse_menu_text(menu_text)
        ]

        review_texts = [review["review_text"] for review in review_metrics["reviews"] if review.get("review_text")]
        image_task = asyncio.create_task(upload_images_with_metrics(seed, resources, crawl_result["photo_urls"]))
        gms_task = asyncio.create_task(
            resolve_gms_enrichment(
                intro=intro,
                review_texts=review_texts,
                gms_client=resources.gms_client,
            )
        )
        (thumbnail_url, cafe_images), (summarized_intro, vibe_tag_ids) = await asyncio.gather(image_task, gms_task)

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


async def _crawl_batch_item(
    *,
    index: int,
    total: int,
    seed: CafeSeed,
    resources: CrawlRequestResources,
    ordered_results: list[OrderedCrawlResult | None],
) -> None:
    logger.info("Cafe crawling item start: [%d/%d] cafe_id=%s name=%s", index + 1, total, seed.cafe_id, seed.name)
    async with resources.batch_semaphore:
        async with track_inflight("cafe"):
            try:
                crawled = await crawl_single_cafe(seed, resources)
            except CafeCrawlingItemError:
                record_result(scope="item", status="item_failure")
                logger.warning("Cafe crawling item missing: cafe_id=%s name=%s", seed.cafe_id, seed.name)
                ordered_results[index] = OrderedCrawlResult(missing_cafe_id=seed.cafe_id)
                return
            except CafeCrawlingSourceError:
                record_result(scope="item", status="source_failure")
                raise

    record_result(scope="item", status="success")
    ordered_results[index] = OrderedCrawlResult(item=crawled)


async def crawl_cafes_batch(request_items: list[CafeCrawlingRequestItem]) -> CafeCrawlingResponse:
    logger.info("Cafe crawling batch start: requested=%s", len(request_items))
    if not request_items:
        record_result(scope="batch", status="success")
        return CafeCrawlingResponse(items=[], total=0, missing_cafe_ids=[])

    runtime_settings = resolve_runtime_settings()
    seeds = [normalize_request_item(item) for item in request_items]
    ordered_results: list[OrderedCrawlResult | None] = [None] * len(seeds)

    async with track_inflight("batch"):
        try:
            async with open_crawl_request_resources(runtime_settings) as resources:
                try:
                    async with asyncio.TaskGroup() as task_group:
                        for index, seed in enumerate(seeds):
                            task_group.create_task(
                                _crawl_batch_item(
                                    index=index,
                                    total=len(seeds),
                                    seed=seed,
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

    raw_items: list[dict[str, Any]] = []
    missing_cafe_ids: list[str] = []
    for result in ordered_results:
        if result is None:
            continue
        if result.missing_cafe_id is not None:
            missing_cafe_ids.append(result.missing_cafe_id)
        elif result.item is not None:
            raw_items.append(result.item)

    items = assign_sequence_ids(raw_items)
    response = CafeCrawlingResponse(
        items=items,
        total=len(items),
        missing_cafe_ids=missing_cafe_ids,
    )
    record_result(scope="batch", status="success")
    logger.info(
        "Cafe crawling batch complete: requested=%s succeeded=%s missing=%s",
        len(request_items),
        response.total,
        len(response.missing_cafe_ids),
    )
    return response
