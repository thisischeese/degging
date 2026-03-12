"""
crawler.py – 네이버 지도 가게 크롤러
Playwright(async) 로 탭별 내용을 수집하고 사진을 저장한다.

[핵심 설계 원칙]
CSS 클래스 셀렉터에 의존하지 않고, 탭마다 직접 URL로 접근한다.
  예) https://pcmap.place.naver.com/restaurant/{place_id}/menu

[출력 디렉터리 구조]
output/{가게명}/
├── texts/
│   ├── home.txt / menu.txt / review.txt / photo.txt / info.txt
└── photos/
    ├── photo_00~09.jpg   (사진 탭)
    ├── menu/             (메뉴별 사진)
    └── review/           (방문자 리뷰 사진)

[캐시 정책]
output/{가게명}/texts/ 또는 photos/ 에 파일이 이미 있으면 스킵.
"""

import asyncio
import random
import re
import urllib.parse
from pathlib import Path

import aiofiles
import httpx
from playwright.async_api import async_playwright, Page, Frame

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
DEFAULT_SEARCH_NAME  = "아우어베이커리 역삼점"
NAVER_MAP_BASE_URL   = "https://map.naver.com/p/search/"
OUTPUT_DIR           = Path(__file__).parent / "output"
MAX_PHOTOS           = 10
MAX_REVIEW_PHOTOS    = 10

# 탭명 → (직접 접근 슬러그, 저장 파일명) 매핑
# 슬러그는 pcmap.place.naver.com/restaurant/{id}/{slug} URL 경로
TAB_CONFIG = {
    "홈":   ("home",        "home"),
    "메뉴": ("menu",        "menu"),
    "리뷰": ("review",      "review"),
    "사진": ("photo",       "photo"),
    "정보": ("information", "info"),
}
TABS = list(TAB_CONFIG.keys())

# 네이버 차단 감지 마커
BLOCK_MARKER = "서비스 이용이 제한"

# 다양한 UA 풀 – 요청마다 랜덤 선택
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

def _random_ua() -> str:
    return random.choice(_UA_POOL)

# 기본 UA (이미지 다운로드 등 단순 httpx 요청에 사용)
UA = _UA_POOL[0]

# 뷰포트 풀 – 컨텍스트마다 랜덤 선택
_VIEWPORT_POOL = [
    {"width": 1400, "height": 900},
    {"width": 1280, "height": 800},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1920, "height": 1080},
]

# ── 네트워크 차단 설정 ──────────────────────────
# 분석/광고/지도타일 도메인을 차단해 페이지 로드 단축
BLOCK_HOSTS = frozenset({
    "mc.naver.com",           # Naver 클릭 분석
    "beagle.naver.com",       # Naver 행동 분석
    "collect.veta.naver.com", # Naver 데이터 수집
    "wcs.naver.com",          # Naver 웹 통계
    "api.vworld.kr",          # 지도 타일 (불필요)
})
# 검색 페이지: 문서·스크립트·XHR·Fetch 만 필요
_BLOCK_SEARCH = frozenset({"image", "font", "media", "stylesheet", "websocket", "other"})
# 탭 페이지: 이미지 URL 수집을 위해 image 타입은 허용
_BLOCK_TAB = frozenset({"font", "media", "websocket", "other"})


# ──────────────────────────────────────────────
# 경로 관리
# ──────────────────────────────────────────────
def _safe_name(name: str) -> str:
    """파일/폴더명으로 쓸 수 없는 문자 및 개행 제거."""
    name = name.replace("\n", " ").replace("\r", "").replace("\t", " ")
    name = re.sub(r'[\\/:*?"<>|]', "_", name)
    return name.strip()


def _get_dirs(search_name: str) -> dict[str, Path]:
    base = OUTPUT_DIR / search_name
    return {
        "base":   base,
        "texts":  base / "texts",
        "photos": base / "photos",
        "menu":   base / "photos" / "menu",
        "review": base / "photos" / "review",
    }


def _ensure_dirs(dirs: dict[str, Path]) -> None:
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)


def _is_blocked_content(dirs: dict[str, Path]) -> bool:
    """저장된 home.txt 가 네이버 차단 메시지를 포함하면 True."""
    home = dirs["texts"] / "home.txt"
    if home.exists():
        try:
            return BLOCK_MARKER in home.read_text(encoding="utf-8")
        except OSError:
            pass
    return False


def _already_crawled(dirs: dict[str, Path]) -> bool:
    """
    texts/ 에 .txt 파일이 하나라도 있으면 이미 크롤링된 것으로 판단.
    photos/ 는 부분 다운로드가 가능하므로 완료 지표로 사용하지 않는다.
    단, 차단 메시지가 저장된 경우는 재크롤링 대상으로 간주해 False 반환.
    """
    base = dirs["base"]
    if not base.exists():
        return False
    # 차단된 캐시는 무효 처리
    if _is_blocked_content(dirs):
        return False
    texts_dir = dirs["texts"]
    return texts_dir.exists() and any(texts_dir.glob("*.txt"))


def _build_cached_result(dirs: dict[str, Path]) -> dict:
    texts    = {p.stem: str(p) for p in dirs["texts"].glob("*.txt")} if dirs["texts"].exists() else {}
    photos   = [str(p) for p in dirs["photos"].glob("thumbnail.*")] if dirs["photos"].exists() else []
    menu_p   = [str(p) for p in dirs["menu"].glob("*")] if dirs["menu"].exists() else []
    review_p = [str(p) for p in dirs["review"].glob("*")] if dirs["review"].exists() else []
    return {"texts": texts, "photos": photos, "menu_photos": menu_p, "review_photos": review_p, "cached": True}


# ──────────────────────────────────────────────
# 페이지 네트워크 차단
# ──────────────────────────────────────────────
async def _configure_page(page: Page, *, search_mode: bool = False) -> None:
    """
    불필요한 리소스·분석 도메인 요청을 차단해 페이지 로드를 가속한다.

    search_mode=True  : 검색 페이지 (image/stylesheet 포함 전면 차단)
    search_mode=False : 탭 콘텐츠 페이지 (이미지 URL 수집 필요 → image 허용)
    """
    block_types = _BLOCK_SEARCH if search_mode else _BLOCK_TAB

    async def _handle(route):
        url = route.request.url
        if (any(h in url for h in BLOCK_HOSTS)
                or route.request.resource_type in block_types):
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", _handle)


# ──────────────────────────────────────────────
# 이미지 다운로드 헬퍼
# ──────────────────────────────────────────────
async def _download_image(
    client: httpx.AsyncClient,
    url: str,
    dest: Path,
    referer: str = "https://pcmap.place.naver.com/",
) -> Path | None:
    try:
        resp = await client.get(
            url,
            headers={"User-Agent": UA, "Referer": referer},
            timeout=20,
        )
        resp.raise_for_status()
        async with aiofiles.open(dest, "wb") as f:
            await f.write(resp.content)
        return dest
    except Exception as e:
        print(f"    [WARN] 다운로드 실패 ({url[:60]}): {e}")
        return None


def _make_dest(base_dir: Path, index: int, label: str, url: str, prefix: str = "") -> Path:
    clean = url.split("?")[0]
    ext = Path(clean).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        ext = ".jpg"
    safe = _safe_name(label) if label else ""
    fname = f"{prefix}{index:02d}_{safe}{ext}" if safe else f"{prefix}{index:02d}{ext}"
    return base_dir / fname


# ──────────────────────────────────────────────
# Place ID 추출
# ──────────────────────────────────────────────
def _place_url_from_all_search(data: dict) -> str | None:
    """
    allSearch API JSON에서 첫 번째 place 결과의 pcmap base URL을 반환한다.

    카페/식음료 업종은 모두 restaurant 경로를 사용한다.
    """
    try:
        items = data["result"]["place"]["list"]
        if items:
            place_id = items[0]["id"]
            return f"https://pcmap.place.naver.com/restaurant/{place_id}"
    except (KeyError, TypeError, IndexError):
        pass
    return None


async def _extract_place_url(page: Page, timeout_sec: int = 20) -> str | None:
    """
    entryIframe URL 에서 place base URL을 추출한다. (폴백용)
    예) https://pcmap.place.naver.com/restaurant/1778692759/home
      → https://pcmap.place.naver.com/restaurant/1778692759
    """
    for _ in range(timeout_sec):
        for frame in page.frames:
            if "entryIframe" in (frame.name or ""):
                m = re.search(
                    r"(https://pcmap\.place\.naver\.com/[a-z]+/\d+)",
                    frame.url,
                )
                if m:
                    return m.group(1)
        await asyncio.sleep(1)
    return None


# ──────────────────────────────────────────────
# 탭 페이지 직접 접근 & 텍스트 추출
# ──────────────────────────────────────────────
async def _fetch_tab(page: Page, tab_url: str) -> str:
    """
    탭 URL로 직접 이동 후 body 전체 텍스트를 반환한다.
    특정 CSS 클래스 셀렉터에 의존하지 않는다.
    """
    await page.goto(tab_url, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(3)  # JS 렌더링 대기

    # JavaScript로 body innerText 추출 → 클래스명 불필요
    text: str = await page.evaluate("() => document.body.innerText")
    return text.strip()


# ──────────────────────────────────────────────
# 이미지 URL 수집 (공통)
# ──────────────────────────────────────────────
async def _collect_cdn_images(page: Page, scroll_steps: int = 6) -> list[str]:
    """
    현재 페이지에서 스크롤하며 네이버 CDN 이미지 URL을 수집한다.
    src 속성 기반만 사용 (클래스명 불필요).
    """
    collected: set[str] = set()

    def _on_request(req):
        if req.resource_type == "image":
            url = req.url
            if any(cdn in url for cdn in ["pstatic.net", "naver.net"]):
                collected.add(url.split("?")[0])

    page.on("request", _on_request)
    try:
        for _ in range(scroll_steps):
            await page.evaluate("window.scrollBy(0, 600)")
            await asyncio.sleep(1.0)

        # img[src] 속성으로 직접 수집 (클래스 무관)
        srcs: list[str] = await page.evaluate("""
            () => Array.from(document.querySelectorAll('img[src]'))
                       .map(img => img.src)
                       .filter(src => src && !src.startsWith('data:'))
        """)
        for src in srcs:
            if any(cdn in src for cdn in ["pstatic.net", "naver.net"]):
                hq = re.sub(r"/thumbnail/\d+x\d+(?:crop)?/", "/", src)
                collected.add(hq.split("?")[0])
    finally:
        page.remove_listener("request", _on_request)

    return [
        u for u in collected
        if not u.endswith((".svg", ".gif", ".ico"))
    ]


# ──────────────────────────────────────────────
# 메뉴 사진 수집
# ──────────────────────────────────────────────
async def _collect_menu_photos(page: Page) -> list[dict]:
    """
    메뉴 페이지에서 JavaScript로 메뉴명 + 사진 URL 쌍을 추출한다.
    클래스 셀렉터 대신 DOM 구조(링크 > 텍스트 + 이미지) 기반.
    """
    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(2)

    items: list[dict] = await page.evaluate("""
        () => {
            const results = [];
            // "대표", "BEST" 같은 레이블 및 가격 패턴 제외 토큰
            const SKIP = new Set(['대표', 'best', 'new', '인기', '추천', '품절', '준비중']);
            const PRICE_RE = /^[\\d,]+(원)?$/;

            const anchors = document.querySelectorAll('a');
            for (const a of anchors) {
                // 갤러리/사진 더보기 버튼 제외 (place_thumb 클래스 포함 시 메뉴 아이템 아님)
                const aClass = (a.className || '') + ' ' + (a.querySelector('[class]')?.className || '');
                if (aClass.includes('place_thumb') || aClass.includes('photo_area')) continue;

                const img = a.querySelector('img[src]');
                if (!img) continue;
                const src = img.src || '';
                if (!src || src.startsWith('data:')) continue;
                // 메뉴 사진은 ldb-phinf.pstatic.net CDN 또는 그 프록시 URL만 허용
                const isMenuImg = src.includes('ldb-phinf.pstatic.net') ||
                    (src.includes('search.pstatic.net') && src.includes('ldb-phinf'));
                if (!isMenuImg) continue;

                // innerText를 줄바꿈 분리 후 메뉴명 추출
                // 텍스트 노드 순서: ["대표"(선택), "메뉴명", "설명", "가격"]
                // → 레이블/가격을 건너뛰어 첫 번째 짧은 텍스트가 메뉴명
                const lines = (a.innerText || '')
                    .split('\\n')
                    .map(s => s.trim())
                    .filter(Boolean);

                let name = '';
                for (const line of lines) {
                    if (SKIP.has(line.toLowerCase())) continue;  // 레이블 스킵
                    if (PRICE_RE.test(line)) continue;           // 가격 스킵
                    if (line.length > 30) continue;             // 설명문(긴 문장) 스킵
                    name = line;
                    break;
                }
                if (!name) continue;

                // search.pstatic.net 프록시 URL → 원본 URL 추출
                let finalUrl = src;
                try {
                    const u = new URL(src);
                    const origSrc = u.searchParams.get('src');
                    if (origSrc) finalUrl = origSrc;
                } catch(e) {}

                results.push({ name, url: finalUrl.split('?')[0] });
            }
            // 중복 제거 (url 기준)
            const seen = new Set();
            return results.filter(r => {
                if (seen.has(r.url)) return false;
                seen.add(r.url);
                return true;
            });
        }
    """)


    print(f"    메뉴 아이템 {len(items)}개 발견")
    for i, item in enumerate(items):
        print(f"      [{i+1}] {item['name']} → URL 확보")
    return items


# ──────────────────────────────────────────────
# 메인 크롤러
# ──────────────────────────────────────────────
async def run_crawl(search_name: str = DEFAULT_SEARCH_NAME) -> dict:
    """
    가게명으로 네이버 지도를 검색 후 탭별 URL에 직접 접근해 크롤링 실행.

    :param search_name: 검색할 가게명 (예: '아우어베이커리 역삼점')
    :returns: 저장된 파일 경로 딕셔너리
    """
    search_url = NAVER_MAP_BASE_URL + urllib.parse.quote(search_name)
    dirs = _get_dirs(search_name)

    # 캐시 체크
    if _already_crawled(dirs):
        print(f"[SKIP] '{search_name}' 크롤링 결과가 이미 존재합니다. ({dirs['base']})")
        return _build_cached_result(dirs)

    _ensure_dirs(dirs)
    results: dict = {"texts": {}, "photos": [], "menu_photos": [], "review_photos": []}

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        session_ua = _random_ua()
        session_viewport = random.choice(_VIEWPORT_POOL)
        context = await browser.new_context(
            viewport=session_viewport,
            user_agent=session_ua,
            locale="ko-KR",
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # ── 1. 검색 페이지 → place base URL 추출 ──
        # allSearch API 응답 인터셉트로 place ID를 빠르게 획득.
        # 기존: sleep(8) + iframe 폴링 ≒ 11~40초 → 신규: ~5초
        map_page = await context.new_page()
        await _configure_page(map_page, search_mode=True)
        all_search_data: dict = {}

        async def _on_all_search(response):
            if "allSearch" in response.url and "data" not in all_search_data:
                try:
                    all_search_data["data"] = await response.json()
                except Exception:
                    pass

        map_page.on("response", _on_all_search)

        print(f"[1] 검색 URL 접속: {search_url}")
        # "commit" = 서버 응답 헤더 수신 직후 리턴 (~0.07s).
        # allSearch는 commit 이후 ~2~4s에 수신되므로 루프를 8초로 확장.
        await map_page.goto(search_url, wait_until="commit", timeout=25000)

        print("[2] allSearch API 응답 대기 (최대 8초)…")
        for _ in range(8):
            if "data" in all_search_data:
                break
            await asyncio.sleep(1)

        place_base_url: str | None = None

        if "data" in all_search_data:
            place_base_url = _place_url_from_all_search(all_search_data["data"])
            if place_base_url:
                print(f"    [allSearch] place URL 획득: {place_base_url}")

        # 폴백: entryIframe 감지 (allSearch 실패 또는 CAPTCHA 차단 시)
        if not place_base_url:
            print("    allSearch 미획득 → entryIframe 폴백 (최대 15초)…")
            place_base_url = await _extract_place_url(map_page, timeout_sec=15)

            # searchIframe 첫 결과 클릭 → entryIframe 네비게이션 이벤트로 즉시 감지
            # sleep(5) + 폴링 방식 대신 framenavigated 이벤트 리스너로 대기 제거
            if not place_base_url:
                print("    searchIframe 첫 결과 클릭 (framenavigated 이벤트 대기)…")
                for frame in map_page.frames:
                    if "searchIframe" not in (frame.name or ""):
                        continue
                    try:
                        url_future: asyncio.Future = asyncio.get_event_loop().create_future()

                        def _on_frame_nav(nav_frame):
                            m = re.search(
                                r"(https://pcmap\.place\.naver\.com/[a-z]+/\d+)",
                                nav_frame.url or "",
                            )
                            if m and not url_future.done():
                                url_future.set_result(m.group(1))

                        map_page.on("framenavigated", _on_frame_nav)
                        try:
                            await frame.locator("li a").first.click(timeout=8000)
                            place_base_url = await asyncio.wait_for(url_future, timeout=10)
                        except asyncio.TimeoutError:
                            print("    [WARN] 클릭 후 entryIframe 로드 타임아웃")
                        finally:
                            map_page.remove_listener("framenavigated", _on_frame_nav)
                    except Exception as e:
                        print(f"    [WARN] searchIframe 클릭 실패: {e}")
                    break

        if not place_base_url:
            raise RuntimeError(
                "place base URL을 찾지 못했습니다. 검색 결과가 없거나 네이버 지도 구조가 변경되었을 수 있습니다."
            )
        print(f"    place URL: {place_base_url}")
        await map_page.close()

        # ── 2. 탭별 직접 URL 접근 ─────────────────
        # 탭 크롤링 전용 페이지 (재사용)
        tab_page = await context.new_page()
        await _configure_page(tab_page, search_mode=False)
        print("\n[3] 탭별 URL 직접 접근 시작")

        photo_tab_urls: list[str]    = []
        review_photo_urls: list[str] = []

        for tab_name, (slug, fname) in TAB_CONFIG.items():
            tab_url = f"{place_base_url}/{slug}"
            print(f"\n  → [{tab_name}]  {tab_url}")

            # 탭 URL로 직접 이동
            text = await _fetch_tab(tab_page, tab_url)

            # 탭별 추가 처리
            if tab_name == "사진":
                photo_tab_urls = await _collect_cdn_images(tab_page, scroll_steps=1)
                print(f"    사진 URL {len(photo_tab_urls)}개 수집 (첫 번째만 저장)")

            elif tab_name == "메뉴":
                menu_items = await _collect_menu_photos(tab_page)
                if menu_items:
                    async with httpx.AsyncClient() as client:
                        tasks = [
                            _download_image(
                                client,
                                item["url"],
                                _make_dest(dirs["menu"], i, item["name"], item["url"]),
                            )
                            for i, item in enumerate(menu_items)
                        ]
                        downloaded = await asyncio.gather(*tasks)
                    results["menu_photos"] = [str(p) for p in downloaded if p]
                    print(f"    메뉴 사진 {len(results['menu_photos'])}장 저장")

            elif tab_name == "리뷰":
                review_photo_urls = await _collect_cdn_images(tab_page, scroll_steps=8)
                print(f"    리뷰 사진 URL {len(review_photo_urls)}개 수집")

            # 텍스트 저장
            txt_path = dirs["texts"] / f"{fname}.txt"
            async with aiofiles.open(txt_path, "w", encoding="utf-8") as f:
                await f.write(text)
            results["texts"][tab_name] = str(txt_path)
            print(f"    저장: {txt_path} ({len(text)}자)")

            # 탭 간 랜덤 딜레이 (봇 패턴 탐지 회피)
            tab_delay = random.uniform(3.0, 8.0)
            print(f"    탭 간 대기: {tab_delay:.1f}초")
            await asyncio.sleep(tab_delay)

        await tab_page.close()

        # ── 3. 사진 탭 thumbnail 다운로드 ────────
        if photo_tab_urls:
            first_url = photo_tab_urls[0]
            clean = first_url.split("?")[0]
            ext = Path(clean).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
                ext = ".jpg"
            dest = dirs["photos"] / f"thumbnail{ext}"
            print(f"\n[4] 사진 탭 thumbnail 다운로드…")
            async with httpx.AsyncClient() as client:
                downloaded = await _download_image(client, first_url, dest)
            if downloaded:
                results["photos"] = [str(downloaded)]
                print(f"    저장: {downloaded}")

        # ── 4. 리뷰 사진 다운로드 ────────────────
        if review_photo_urls:
            targets = review_photo_urls[:MAX_REVIEW_PHOTOS]
            print(f"\n[5] 리뷰 사진 다운로드 ({len(targets)}장)…")
            async with httpx.AsyncClient() as client:
                tasks = [
                    _download_image(
                        client,
                        url,
                        _make_dest(dirs["review"], i, "", url, prefix="review_"),
                    )
                    for i, url in enumerate(targets)
                ]
                downloaded = await asyncio.gather(*tasks)
            results["review_photos"] = [str(p) for p in downloaded if p]
            print(f"    리뷰 사진 {len(results['review_photos'])}장 저장")

        await browser.close()

    print("\n[완료] 크롤링 완료")
    return results
