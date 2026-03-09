"""
test_search.py – cafes.json 전체 카페 SEARCH_URL 존재 여부 테스트

[존재 판단 기준]
  네이버 지도에서 카페명으로 검색했을 때 entryIframe(place 상세 페이지)이
  자동 로드되면 "존재"로 판정.
  이는 crawler.py의 place URL 추출 로직과 동일한 기준이다.

[결과 파일]  data/cafe_search_results.json
  [
    {
      "name": "카페명",
      "search_url": "https://map.naver.com/p/search/...",
      "exists": true,
      "place_url": "https://pcmap.place.naver.com/restaurant/1234567",
      "checked_at": "2026-03-04T07:00:00+00:00",
      "error": null
    }, ...
  ]

[실행]
  python test_search.py                  # 기본 동시성 3
  python test_search.py --concurrency 5  # 동시성 조정
  python test_search.py --limit 100      # 최대 N개만 테스트
"""

import argparse
import asyncio
import json
import re
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright, BrowserContext, Page

# ── 설정 ──────────────────────────────────────────────────────────────────────
DATA_DIR         = Path(__file__).parent / "data"
CAFES_JSON       = DATA_DIR / "cafes.json"
RESULTS_JSON     = DATA_DIR / "cafe_search_results.json"

NAVER_MAP_BASE_URL = "https://map.naver.com/p/search/"
DEFAULT_CONCURRENCY = 3   # 동시 검사 수 (높이면 차단 위험)
IFRAME_TIMEOUT      = 8   # entryIframe 자동 로드 대기(초)
SAVE_INTERVAL       = 50  # N개 완료마다 중간 저장

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# ── 네트워크 차단 설정 ─────────────────────────────────────────────────────────
# 분석/광고/지도타일 도메인 + 불필요한 리소스 타입을 차단해 domcontentloaded 단축
BLOCK_HOSTS = frozenset({
    "mc.naver.com",           # Naver 클릭 분석
    "beagle.naver.com",       # Naver 행동 분석
    "collect.veta.naver.com", # Naver 데이터 수집
    "wcs.naver.com",          # Naver 웹 통계
    "api.vworld.kr",          # 지도 타일 (불필요)
})
# 존재 여부 확인에 문서·스크립트·XHR·Fetch 만 필요; 나머지 모두 차단
BLOCK_TYPES = frozenset({"image", "font", "media", "stylesheet", "websocket", "other"})


# ── 페이지 네트워크 차단 설정 ─────────────────────────────────────────────────
async def _configure_page(page: Page) -> None:
    """불필요한 리소스·분석 도메인 요청을 차단해 페이지 로드를 가속한다."""
    async def _handle(route):
        url = route.request.url
        if (any(h in url for h in BLOCK_HOSTS)
                or route.request.resource_type in BLOCK_TYPES):
            await route.abort()
        else:
            await route.continue_()
    await page.route("**/*", _handle)


# ── entryIframe 감지 (폴백용) ─────────────────────────────────────────────────
async def _detect_entry_frame(page: Page, timeout_sec: int) -> str | None:
    """entryIframe의 place base URL을 최대 timeout_sec 초 대기 후 반환."""
    for _ in range(timeout_sec):
        for frame in page.frames:
            m = re.search(
                r"(https://pcmap\.place\.naver\.com/[a-z]+/\d+)",
                frame.url or "",
            )
            if m:
                return m.group(1)
        await asyncio.sleep(1)
    return None


# ── allSearch JSON → place URL 추출 ──────────────────────────────────────────
def _place_url_from_all_search(data: dict) -> str | None:
    """
    allSearch API JSON에서 첫 번째 place 결과의 pcmap URL을 반환한다.

    place.list[0].id 가 존재하면 restaurant 타입으로 URL 구성.
    (카페/베이커리 등 식음료 업종은 모두 restaurant 경로 사용)
    """
    try:
        items = data["result"]["place"]["list"]
        if items:
            place_id = items[0]["id"]
            return f"https://pcmap.place.naver.com/restaurant/{place_id}"
    except (KeyError, TypeError, IndexError):
        pass
    return None


# ── 개별 카페 검사 ────────────────────────────────────────────────────────────
async def check_one(
    context: BrowserContext,
    sem: asyncio.Semaphore,
    name: str,
) -> dict:
    """
    allSearch API 응답 인터셉트로 place 존재 여부 판단.

    기존: goto + sleep(8초) + iframe 폴링(최대 8초) ≒ 11~19초/건
    신규: goto + allSearch 인터셉트 ≒ 4~6초/건 (2~3배 단축)

    allSearch 응답이 오지 않으면 iframe 폴백(3초)을 사용한다.
    """
    search_url = NAVER_MAP_BASE_URL + urllib.parse.quote(name)
    result = {
        "name": name,
        "search_url": search_url,
        "exists": False,
        "place_url": None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }

    captured: dict = {}

    async with sem:
        page = await context.new_page()
        await _configure_page(page)
        try:
            # allSearch 응답 인터셉트
            async def _on_response(response):
                if "allSearch" in response.url and "captured" not in captured:
                    try:
                        captured["data"] = await response.json()
                    except Exception:
                        pass

            page.on("response", _on_response)
            # "commit" = 서버 응답 헤더 수신 직후 (~0.07s) 리턴.
            # domcontentloaded(~1~2.7s)를 기다리지 않으므로 goto()가 asyncio
            # 이벤트 루프를 2~3초 일찍 반환 → 동시 처리 시 throughput 향상.
            # allSearch는 commit 이후 ~1.7~4.2s 뒤에 수신되므로 루프를 8초로 확장.
            await page.goto(search_url, wait_until="commit", timeout=20000)

            # allSearch 응답 대기 (최대 8초 – commit 기준으로 여유 확보)
            for _ in range(8):
                if "data" in captured:
                    break
                await asyncio.sleep(1)

            if "data" in captured:
                place_url = _place_url_from_all_search(captured["data"])
                result["exists"] = place_url is not None
                result["place_url"] = place_url
            else:
                # 폴백: entryIframe 감지 (3초)
                place_url = await _detect_entry_frame(page, 3)
                result["exists"] = place_url is not None
                result["place_url"] = place_url

        except Exception as e:
            result["error"] = str(e)
        finally:
            await page.close()

    return result


# ── 저장 ─────────────────────────────────────────────────────────────────────
def _load_done() -> dict[str, dict]:
    if RESULTS_JSON.exists():
        data = json.loads(RESULTS_JSON.read_text(encoding="utf-8"))
        return {r["name"]: r for r in data}
    return {}


def _save(done: dict[str, dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    results = sorted(done.values(), key=lambda r: r["name"])
    RESULTS_JSON.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── 메인 ─────────────────────────────────────────────────────────────────────
async def run_tests(concurrency: int, limit: int | None) -> None:
    cafes: list[str] = json.loads(CAFES_JSON.read_text(encoding="utf-8"))
    if limit:
        cafes = cafes[:limit]
    total = len(cafes)

    # 재시작 지원: 이미 완료된 항목 스킵
    done = _load_done()
    remaining = [c for c in cafes if c not in done]
    print(f"총 {total}개 | 완료 {len(done)}개 | 남은 {len(remaining)}개 | 동시성 {concurrency}")
    if not remaining:
        print("모두 완료되었습니다.")
        _print_summary(done)
        return

    sem = asyncio.Semaphore(concurrency)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=UA,
            locale="ko-KR",
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        tasks = [check_one(context, sem, name) for name in remaining]
        finished = 0

        for coro in asyncio.as_completed(tasks):
            result = await coro
            done[result["name"]] = result
            finished += 1

            # 상태 기호: O=발견 / X=미발견 / E=오류
            status = "E" if result["error"] else ("O" if result["exists"] else "X")
            place_info = f" → {result['place_url']}" if result["place_url"] else ""
            print(
                f"  [{finished:>5}/{len(remaining)}] [{status}] "
                f"{result['name'][:30]:<30}{place_info}"
            )

            if finished % SAVE_INTERVAL == 0:
                _save(done)
                found = sum(1 for r in done.values() if r["exists"])
                print(f"  [중간 저장] {found}/{len(done)} 발견")

        _save(done)
        await browser.close()

    _print_summary(done)
    print(f"\n결과 파일: {RESULTS_JSON}")


def _print_summary(done: dict[str, dict]) -> None:
    total   = len(done)
    found   = sum(1 for r in done.values() if r["exists"])
    not_found = sum(1 for r in done.values() if not r["exists"] and not r["error"])
    errors  = sum(1 for r in done.values() if r["error"])
    print(f"\n{'─'*40}")
    print(f"[결과 요약]")
    print(f"  전체    : {total:>6}개")
    print(f"  존재    : {found:>6}개")
    print(f"  미발견  : {not_found:>6}개")
    print(f"  오류    : {errors:>6}개")
    print(f"{'─'*40}")


# ── 진입점 ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="cafes.json SEARCH_URL 존재 테스트")
    parser.add_argument(
        "--concurrency", type=int, default=DEFAULT_CONCURRENCY,
        help=f"동시 검사 수 (기본: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="테스트할 최대 카페 수 (기본: 전체)",
    )
    args = parser.parse_args()
    asyncio.run(run_tests(concurrency=args.concurrency, limit=args.limit))
