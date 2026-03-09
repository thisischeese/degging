"""
to_csv.py – 크롤링 txt 파일 → 4개 CSV

[출력 파일]
  data/place.csv          – Item Tower 최종 입력 (카페 1개당 1행)
  data/menu.csv           – 메뉴 원본 (place_id FK)
  data/visitor_review.csv – 방문자 리뷰 원본 (place_id FK)
  data/blog_review.csv    – 블로그 리뷰 원본 (place_id FK)

[집계 스텝]
  A: menu.csv          → place.csv  (메뉴 집계)
  B: visitor_review.csv → place.csv (텍스트 + 방문 맥락 집계)
  C: blog_review.csv   → place.csv  (블로그 텍스트 집계)
"""

import csv
import json
import re
import uuid
from collections import Counter
from pathlib import Path
from statistics import mean

OUTPUT_DIR = Path(__file__).parent / "output"
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── 공통 상수 ───────────────────────────────────────────────────────────────

NAV_TABS = {"홈", "메뉴", "리뷰", "사진", "정보"}

LABEL_TOKENS = {
    "대표", "best", "new", "인기", "추천", "품절", "준비중", "best seller",
    "BEST", "NEW", "사진",
}

PRICE_RE = re.compile(r"^[\d,]+(원)?$")
MENU_STOP_PHRASES = ("메뉴 항목과 가격은", "메뉴판 이미지로 보기", "이용약관")

# "리뷰 36사진 14팔로워 1" / "리뷰 1,375사진 679" 등
REVIEWER_STATS_RE = re.compile(r"^리뷰\s+[\d,]+")

# "25.12.18.목" (YY.MM.DD.요일) 또는 "1.2.금" (MM.DD.요일, 연도 생략)
SHORT_DATE_RE = re.compile(r"^\d{2}\.\d{1,2}\.\d{1,2}\.\S+$|^\d{1,2}\.\d{1,2}\.\S+$")
LONG_DATE_RE  = re.compile(r"^\d{4}년 \d+월 \d+일")
VISIT_NTH_RE  = re.compile(r"^(\d+)번째 방문$")
TAG_RE        = re.compile(r"^(.+?)(\d+)$")
QUOTE_KW_RE   = re.compile(r'^"(.+)"$')
KW_PLUS_RE    = re.compile(r"^(.+?)\+(\d+)$")

KNOWN_KEYWORDS = {
    "빵이 맛있어요",
    "커피가 맛있어요",
    "매장이 청결해요",
    "인테리어가 멋져요",
    "특별한 메뉴가 있어요",
}

PURPOSE_WORDS   = ["일상", "데이트", "친목", "비즈니스", "기념일"]
COMPANION_WORDS = ["혼자", "연인・배우자", "연인·배우자", "친구", "지인・동료", "지인·동료", "가족", "기타"]

AMENITY_MAP = {
    "포장":           "amenity_takeout",
    "무선 인터넷":    "amenity_wifi",
    "배달":           "amenity_delivery",
    "단체 이용 가능": "amenity_group",
    "남/녀 화장실 구분": "amenity_separate_restroom",
}

CONTROL_LINES = {
    "더보기", "펼쳐보기", "반응 남기기", "팔로우",
    "표정을 눌러 반응을 남겨 보세요!", "명",
    "방문일", "인증 수단",
}


# ── 유틸 ────────────────────────────────────────────────────────────────────

def _place_id(cafe_name: str) -> str:
    ns = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    return str(uuid.uuid5(ns, cafe_name))


def _read(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]


def _skip_header(lines: list[str]) -> int:
    """NAV_TABS 5개가 모두 등장한 직후 인덱스를 반환한다."""
    found: set[str] = set()
    for i, line in enumerate(lines):
        if line in NAV_TABS:
            found.add(line)
            if found == NAV_TABS:
                return i + 1
    return 0


def _normalize_short_date(s: str) -> str | None:
    """'25.12.18.목' → '2025-12-18', '1.2.금' → '2026-01-02'"""
    m = re.match(r"^(\d{2})\.(\d{1,2})\.(\d{1,2})\.", s)
    if m:
        return f"20{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.", s)
    if m:
        return f"2026-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


# ── info.txt 파서 ────────────────────────────────────────────────────────────

def parse_info(lines: list[str]) -> dict:
    result: dict = {
        "business_description": None,
        "amenity_takeout": False,
        "amenity_wifi": False,
        "amenity_delivery": False,
        "amenity_group": False,
        "amenity_separate_restroom": False,
        "parking": None,
        "sns_url": None,
    }

    start = _skip_header(lines)
    body  = lines[start:]

    # 소개 텍스트: "소개" 이후 ~ 다음 섹션("편의시설") 전
    desc_lines: list[str] = []
    in_desc = False
    for line in body:
        if line == "소개":
            in_desc = True
            continue
        if in_desc:
            if not line or line.startswith("편의시설"):
                in_desc = False
                continue
            desc_lines.append(line)
    if desc_lines:
        result["business_description"] = " ".join(desc_lines)

    # 편의시설, 주차, SNS
    for line in body:
        for key, col in AMENITY_MAP.items():
            if key == line:
                result[col] = True

        if line == "주차 불가":
            result["parking"] = "주차 불가"
        elif line == "주차 가능":
            result["parking"] = "주차 가능"

        if (line.startswith("https://") or line.startswith("http://")) and not result["sns_url"]:
            result["sns_url"] = line

    return result


# ── home.txt 파서 ────────────────────────────────────────────────────────────

def parse_home(lines: list[str]) -> tuple[dict, list[dict]]:
    """
    Returns:
        result: 정적 피처 + 키워드 집계
        blog_reviews: 블로그 리뷰 목록
    """
    result: dict = {
        "place_name":           None,
        "category":             None,
        "image_count":          None,
        "visitor_review_count": None,
        "blog_review_count":    None,
        "address":              None,
        "district":             None,
        "nearby_station":       None,
        "station_distance_m":   None,
        "phone":                None,
        "sns_url":              None,
        "weekday_hours":        None,
        "weekend_hours":        None,
        "kw_bread_tasty":   0,
        "kw_coffee_tasty":  0,
        "kw_clean":         0,
        "kw_interior":      0,
        "kw_unique_menu":   0,
    }

    # place_name (line index 1)
    if len(lines) > 1:
        result["place_name"] = lines[1]

    # 헤더에서 카테고리, 이미지 수, 리뷰 수 추출 (앞 15줄)
    for line in lines[:15]:
        m = re.search(r"(베이커리|카페|레스토랑|음식점|바|펍|디저트)$", line)
        if m and result["category"] is None:
            result["category"] = m.group(1)

        if re.match(r"^\d{2,}\+?$", line) and result["image_count"] is None:
            result["image_count"] = int(line.replace("+", ""))

        m = re.search(r"방문자 리뷰\s*(\d+)블로그 리뷰\s*(\d+)", line)
        if m:
            result["visitor_review_count"] = int(m.group(1))
            result["blog_review_count"]    = int(m.group(2))

    # 전체 스캔
    pending_kw: str | None = None
    for i, line in enumerate(lines):
        # 주소
        if (
            re.match(r"^(서울|경기|인천|부산|대구|대전|광주|울산|세종|강원|충북|충남|전북|전남|경북|경남|제주)", line)
            and result["address"] is None
        ):
            result["address"] = line
            m = re.search(r"(\S+구|\S+시)", line)
            if m:
                result["district"] = m.group(1)

        # 역 접근성: "2역삼역 1번 출구에서 428m" → 숫자 접두 제거
        m = re.search(r"(\S+역\s*\d+번\s*출구)에서\s*(\d+)m", line)
        if m and result["nearby_station"] is None:
            result["nearby_station"]     = m.group(1)
            result["station_distance_m"] = int(m.group(2))

        # 전화번호
        m = re.match(r"^(0\d{1,4}-\d{3,4}-\d{4})$", line)
        if m and result["phone"] is None:
            result["phone"] = m.group(1)

        # SNS URL
        if line.startswith("http") and result["sns_url"] is None:
            result["sns_url"] = line

        # 편의시설 (쉼표 구분 한 줄)
        if any(key in line for key in AMENITY_MAP):
            parts = re.split(r",\s*", line)
            for part in parts:
                for key, col in AMENITY_MAP.items():
                    if key in part:
                        result[col] = True

        # 키워드 집계: "빵이 맛있어요" → 이 키워드를 선택한 인원 → 숫자
        qm = QUOTE_KW_RE.match(line)
        if qm:
            pending_kw = qm.group(1)

        if line == "이 키워드를 선택한 인원" and pending_kw:
            if i + 1 < len(lines) and re.match(r"^\d+$", lines[i + 1]):
                count = int(lines[i + 1])
                kw    = pending_kw
                if "빵이 맛있어요"    in kw: result["kw_bread_tasty"]  = count
                elif "커피가 맛있어요" in kw: result["kw_coffee_tasty"] = count
                elif "청결"           in kw: result["kw_clean"]         = count
                elif "인테리어"       in kw: result["kw_interior"]      = count
                elif "특별한 메뉴"    in kw: result["kw_unique_menu"]   = count
                pending_kw = None

    # 블로그 리뷰
    blog_reviews = _parse_blog_reviews(lines)

    # 영업시간 추출 (블로그 본문에서)
    for br in blog_reviews:
        body = br.get("post_body") or ""
        if not result["weekday_hours"]:
            m = re.search(r"월.{0,2}화.{0,2}수.{0,2}목.{0,2}금\s*(\d{2}:\d{2})\s*[–\-~]\s*(\d{2}:\d{2})", body)
            if m:
                result["weekday_hours"] = f"{m.group(1)}-{m.group(2)}"
        if not result["weekend_hours"]:
            m = re.search(r"토.{0,2}일\s*(\d{2}:\d{2})\s*[–\-~]\s*(\d{2}:\d{2})", body)
            if m:
                result["weekend_hours"] = f"{m.group(1)}-{m.group(2)}"

    return result, blog_reviews


def _parse_blog_reviews(lines: list[str]) -> list[dict]:
    """home.txt에서 블로그 리뷰 블록을 파싱한다."""
    # "블로그 리뷰124" 이후를 blog_body로 사용
    blog_start = -1
    for i, line in enumerate(lines):
        if re.match(r"^블로그 리뷰\d+", line):
            blog_start = i + 1
            break
    if blog_start == -1:
        return []

    body = lines[blog_start:]

    # SHORT_DATE 바로 다음에 LONG_DATE가 오는 지점을 앵커로 찾는다
    date_anchors: list[int] = []
    for i in range(len(body) - 1):
        if SHORT_DATE_RE.match(body[i]) and LONG_DATE_RE.match(body[i + 1]):
            date_anchors.append(i)

    if not date_anchors:
        return []

    reviews: list[dict] = []
    for j, da in enumerate(date_anchors):
        # 이번 리뷰 블록: 이전 앵커+4(이미지수 라인 직후) ~ 현재 앵커 전
        block_start = date_anchors[j - 1] + 4 if j > 0 else 0
        block = [l for l in body[block_start:da] if l]  # 빈 줄 제거

        if len(block) < 2:
            continue

        k = 0
        # blogger 닉네임
        k += 1  # block[0] = blogger (skip – user side)

        # 선택적 클립 정보 "네이버클립 @xxx"
        if k < len(block) and block[k].startswith("네이버클립"):
            k += 1

        # 제목 (짧은 부제목 라인이 먼저 올 수 있어 길이로 구분)
        title = ""
        if k < len(block):
            if len(block[k]) < 25 and k + 1 < len(block):
                k += 1  # 부제목 스킵
            title = block[k]
            k += 1

        # 본문: 나머지 라인들
        body_text = " ".join(block[k:]) if k < len(block) else ""

        # 날짜 정규화
        post_date = _normalize_short_date(body[da]) or body[da]

        # 이미지 수: da+2="이미지 수", da+3=숫자
        img_count = None
        if da + 3 < len(body) and body[da + 2] == "이미지 수":
            try:
                img_count = int(body[da + 3])
            except ValueError:
                pass

        reviews.append({
            "post_title": title,
            "post_body":  body_text,
            "post_date":  post_date,
            "image_count": img_count,
        })

    return reviews


# ── photo.txt 파서 ────────────────────────────────────────────────────────────

def parse_photo(lines: list[str]) -> str:
    start = _skip_header(lines)
    skip  = {
        "이용약관고객센터리뷰운영정책신고센터", "네이버",
        "업체", "클립", "방문자", "블로그",
    }
    categories = [l for l in lines[start:] if l and l not in skip]
    return ",".join(categories)


# ── menu.txt 파서 (db.py 확장: tag·description 포함) ─────────────────────────

def parse_menu(lines: list[str]) -> list[dict]:
    start = _skip_header(lines)

    menus: list[dict] = []
    pending_name: str | None = None
    pending_tag:  str | None = None
    pending_desc: str | None = None

    for line in lines[start:]:
        if not line:
            continue
        if any(line.startswith(s) for s in MENU_STOP_PHRASES):
            break

        # 레이블 태그
        if line.lower() in {t.lower() for t in LABEL_TOKENS}:
            pending_tag = line
            continue

        # 가격 라인
        if PRICE_RE.match(line):
            price_int = int(line.replace("원", "").replace(",", ""))
            if pending_name:
                menus.append({
                    "menu_name":  pending_name,
                    "menu_tag":   pending_tag,
                    "description": pending_desc,
                    "price":      price_int,
                    "price_raw":  line,
                })
                pending_name = pending_tag = pending_desc = None
            continue

        # 메뉴명 후보: 30자 이하 (db.py와 동일 기준)
        if len(line) <= 30:
            if pending_name:
                menus.append({
                    "menu_name":   pending_name,
                    "menu_tag":    pending_tag,
                    "description": pending_desc,
                    "price":       None,
                    "price_raw":   None,
                })
            pending_name = line
            # pending_tag 유지: 직전 레이블("대표" 등)이 이 메뉴를 가리킴
            pending_desc = None
            continue

        # 30자 초과 → 설명문 (현재 pending_name에 귀속)
        pending_desc = line

    # 마지막 메뉴 처리
    if pending_name:
        menus.append({
            "menu_name":  pending_name,
            "menu_tag":   pending_tag,
            "description": pending_desc,
            "price":      None,
            "price_raw":  None,
        })

    return menus


# ── review.txt 파서 ────────────────────────────────────────────────────────────

def parse_review(lines: list[str]) -> tuple[dict, list[dict]]:
    """
    Returns:
        meta:            키워드 집계 + 태그 분포
        visitor_reviews: 방문자 리뷰 목록
    """
    start = _skip_header(lines)
    body  = lines[start:]

    # ── 1. 키워드 집계 ──────────────────────────────────────────────────────
    keyword_counts: dict[str, int] = {}
    i = 0
    while i < len(body):
        qm = QUOTE_KW_RE.match(body[i])
        if qm and i + 2 < len(body) and body[i + 1] == "이 키워드를 선택한 인원":
            try:
                keyword_counts[qm.group(1)] = int(body[i + 2])
                i += 3
                continue
            except ValueError:
                pass
        i += 1

    # ── 2. 태그 분포 ─────────────────────────────────────────────────────────
    menu_tags:    dict[str, int] = {}
    feature_tags: dict[str, int] = {}
    in_menu = in_feature = False

    for line in body:
        if line == "메뉴":
            in_menu, in_feature = True, False
            continue
        if line == "특징":
            in_menu, in_feature = False, True
            continue
        if line in {"추천순", "최신순", "정렬 안내"}:
            in_menu = in_feature = False
            continue

        m = TAG_RE.match(line)
        if m:
            name, count = m.group(1), int(m.group(2))
            if in_menu:
                menu_tags[name] = count
            elif in_feature:
                feature_tags[name] = count

    meta = {
        "kw_bread_tasty":  keyword_counts.get("빵이 맛있어요", 0),
        "kw_coffee_tasty": keyword_counts.get("커피가 맛있어요", 0),
        "kw_clean":        keyword_counts.get("매장이 청결해요", 0),
        "kw_interior":     keyword_counts.get("인테리어가 멋져요", 0),
        "kw_unique_menu":  keyword_counts.get("특별한 메뉴가 있어요", 0),
        "menu_tag_distribution":    json.dumps(menu_tags,    ensure_ascii=False),
        "feature_tag_distribution": json.dumps(feature_tags, ensure_ascii=False),
    }

    # ── 3. 방문자 리뷰 ───────────────────────────────────────────────────────
    review_start = 0
    for i, line in enumerate(body):
        if "리뷰 클렌징" in line:
            review_start = i + 1
            break

    visitor_reviews = _parse_visitor_reviews(body[review_start:])
    return meta, visitor_reviews


def _parse_context(line: str) -> dict:
    """방문맥락 연결 문자열을 파싱한다.
    예: '아침에 방문예약 없이 이용대기 시간 바로 입장일상혼자'
    """
    ctx: dict = {
        "visit_time_of_day": None,
        "reservation":       None,
        "wait_time":         None,
        "visit_purpose":     None,
        "companion_type":    None,
    }

    m = re.search(r"(아침|점심|저녁)에 방문", line)
    if m:
        ctx["visit_time_of_day"] = m.group(1)

    if "예약 없이" in line:
        ctx["reservation"] = False
    elif "예약" in line:
        ctx["reservation"] = True

    m = re.search(
        r"대기 시간\s*(.+?)(?=일상|데이트|친목|비즈니스|기념일|혼자|연인|친구|지인|가족|기타|$)",
        line,
    )
    if m:
        ctx["wait_time"] = m.group(1).strip()

    for pw in PURPOSE_WORDS:
        if pw in line:
            ctx["visit_purpose"] = pw
            break

    for cw in COMPANION_WORDS:
        if cw in line:
            ctx["companion_type"] = cw.replace("・", "·")
            break

    return ctx


def _parse_visitor_reviews(body: list[str]) -> list[dict]:
    """리뷰 블록 경계를 감지 후 각 블록을 파싱한다.
    경계 감지: REVIEWER_STATS_RE에 매칭되는 라인의 직전 라인이 닉네임.
    """
    block_starts: list[int] = []
    for i in range(1, len(body)):
        if REVIEWER_STATS_RE.match(body[i]):
            block_starts.append(i - 1)

    reviews: list[dict] = []
    for j, bs in enumerate(block_starts):
        be    = block_starts[j + 1] if j + 1 < len(block_starts) else len(body)
        block = body[bs:be]
        r     = _parse_single_review(block)
        if r:
            reviews.append(r)
    return reviews


def _parse_single_review(block: list[str]) -> dict | None:
    if len(block) < 4:
        return None

    review: dict = {
        "visit_date":              None,
        "visit_time_of_day":       None,
        "visit_nth":               None,
        "reservation":             None,
        "wait_time":               None,
        "visit_purpose":           None,
        "companion_type":          None,
        "auth_method":             None,
        "review_text":             None,
        "selected_keyword":        None,
        "additional_keyword_count": 0,
        "reaction_count":          0,
    }

    # block[0]: 닉네임 (User Side → 저장 안 함)
    # block[1]: 통계    (User Side → 저장 안 함)
    # block[2]: "팔로우" (skip)
    # block[3]: 방문맥락
    ctx = _parse_context(block[3])
    review.update(ctx)

    # 앵커 인덱스 탐색
    reaction_idx:  int | None = None
    visit_day_idx: int | None = None

    for i, line in enumerate(block):
        if line == "반응 남기기" and reaction_idx is None:
            reaction_idx = i
        elif line == "방문일" and visit_day_idx is None:
            visit_day_idx = i
        elif VISIT_NTH_RE.match(line):
            review["visit_nth"] = int(VISIT_NTH_RE.match(line).group(1))
        elif line == "인증 수단" and i + 1 < len(block):
            nxt = block[i + 1]
            if nxt not in CONTROL_LINES and not REVIEWER_STATS_RE.match(nxt):
                review["auth_method"] = nxt

    # 방문일
    if visit_day_idx is not None and visit_day_idx + 1 < len(block):
        review["visit_date"] = _normalize_short_date(block[visit_day_idx + 1])

    # 반응 수: "반응 남기기" 이후 첫 숫자 라인
    if reaction_idx is not None:
        for i in range(reaction_idx + 1, min(reaction_idx + 4, len(block))):
            if re.match(r"^\d+$", block[i]):
                review["reaction_count"] = int(block[i])
                break

    # 리뷰 본문 + 키워드: block[4] ~ reaction_idx 전까지
    end = reaction_idx if reaction_idx is not None else len(block)
    text_lines: list[str] = []

    for line in block[4:end]:
        if not line or line in CONTROL_LINES:
            continue
        if re.match(r"^\d+$", line):  # 수치 단독 줄 (반응 수 누락분)
            continue
        if line == "개의 리뷰가 더 있습니다":
            continue

        # "빵이 맛있어요+3" 형태
        m = KW_PLUS_RE.match(line)
        if m and m.group(1) in KNOWN_KEYWORDS:
            review["selected_keyword"]         = m.group(1)
            review["additional_keyword_count"] = int(m.group(2))
            continue

        # 단독 키워드
        if line in KNOWN_KEYWORDS:
            review["selected_keyword"] = line
            continue

        # 키워드가 나온 이후 줄은 본문으로 처리하지 않는다
        if review["selected_keyword"] is None:
            text_lines.append(line)

    review["review_text"] = " ".join(text_lines) if text_lines else None
    return review


# ── 집계 스텝 A: 메뉴 → place ──────────────────────────────────────────────

def aggregate_menus(menus: list[dict]) -> dict:
    if not menus:
        return {
            "menu_count":        0,
            "price_min":         None,
            "price_max":         None,
            "price_avg":         None,
            "has_signature_menu": False,
            "menu_names_concat": None,
            "menu_desc_concat":  None,
        }

    prices = [m["price"] for m in menus if m["price"] is not None]
    return {
        "menu_count": len(menus),
        "price_min":  min(prices) if prices else None,
        "price_max":  max(prices) if prices else None,
        "price_avg":  round(mean(prices), 1) if prices else None,
        "has_signature_menu": any(
            (m["menu_tag"] or "").lower() in {"대표", "best"} for m in menus
        ),
        "menu_names_concat": " ".join(m["menu_name"] for m in menus),
        "menu_desc_concat":  " ".join(
            m["description"] for m in menus if m["description"]
        ) or None,
    }


# ── 집계 스텝 B: 방문자 리뷰 → place ─────────────────────────────────────────

def aggregate_visitor_reviews(reviews: list[dict]) -> dict:
    if not reviews:
        return {
            "visitor_review_corpus": None,
            "dominant_visit_time":   None,
            "morning_ratio":         None,
            "lunch_ratio":           None,
            "evening_ratio":         None,
            "dominant_companion":    None,
            "solo_ratio":            None,
            "date_ratio":            None,
            "friend_ratio":          None,
            "dominant_purpose":      None,
            "avg_visit_nth":         None,
        }

    # 본문 코퍼스
    texts  = [r["review_text"] for r in reviews if r["review_text"]]
    corpus = "\n---\n".join(texts) if texts else None

    # 방문 시간대
    times        = [r["visit_time_of_day"] for r in reviews if r["visit_time_of_day"]]
    time_counter = Counter(times)
    total_time   = len(times) or 1

    # 동반자 유형
    companions   = [r["companion_type"] for r in reviews if r["companion_type"]]
    comp_counter = Counter(companions)
    total_comp   = len(companions) or 1

    # 방문 목적
    purposes = [r["visit_purpose"] for r in reviews if r["visit_purpose"]]

    # 방문 차수
    nths = [r["visit_nth"] for r in reviews if r["visit_nth"] is not None]

    return {
        "visitor_review_corpus": corpus,
        "dominant_visit_time":   time_counter.most_common(1)[0][0] if time_counter else None,
        "morning_ratio":         round(time_counter.get("아침", 0) / total_time, 3),
        "lunch_ratio":           round(time_counter.get("점심", 0) / total_time, 3),
        "evening_ratio":         round(time_counter.get("저녁", 0) / total_time, 3),
        "dominant_companion":    comp_counter.most_common(1)[0][0] if comp_counter else None,
        "solo_ratio":            round(comp_counter.get("혼자", 0) / total_comp, 3),
        "date_ratio":            round(comp_counter.get("연인·배우자", 0) / total_comp, 3),
        "friend_ratio":          round(comp_counter.get("친구", 0) / total_comp, 3),
        "dominant_purpose":      Counter(purposes).most_common(1)[0][0] if purposes else None,
        "avg_visit_nth":         round(mean(nths), 2) if nths else None,
    }


# ── 집계 스텝 C: 블로그 리뷰 → place ─────────────────────────────────────────

def aggregate_blog_reviews(blog_reviews: list[dict]) -> dict:
    if not blog_reviews:
        return {"blog_review_corpus": None, "blog_avg_image_count": None}

    bodies = [r["post_body"] for r in blog_reviews if r.get("post_body")]
    counts = [r["image_count"] for r in blog_reviews if r.get("image_count") is not None]
    return {
        "blog_review_corpus":    "\n---\n".join(bodies) if bodies else None,
        "blog_avg_image_count":  round(mean(counts), 1) if counts else None,
    }


# ── CSV 스키마 ────────────────────────────────────────────────────────────────

PLACE_COLS = [
    # 정적 피처
    "place_id", "place_name", "category",
    "address", "district", "nearby_station", "station_distance_m",
    "phone", "sns_url", "business_description",
    "weekday_hours", "weekend_hours", "parking",
    "amenity_takeout", "amenity_wifi", "amenity_delivery",
    "amenity_group", "amenity_separate_restroom",
    "visitor_review_count", "blog_review_count", "image_count",
    "photo_categories",
    # 키워드 집계 (review.txt 기준)
    "kw_bread_tasty", "kw_coffee_tasty", "kw_clean", "kw_interior", "kw_unique_menu",
    "menu_tag_distribution", "feature_tag_distribution",
    # 집계 A (메뉴)
    "menu_count", "price_min", "price_max", "price_avg",
    "has_signature_menu", "menu_names_concat", "menu_desc_concat",
    # 집계 B (방문자 리뷰 텍스트 + 방문 맥락)
    "visitor_review_corpus",
    "dominant_visit_time", "morning_ratio", "lunch_ratio", "evening_ratio",
    "dominant_companion", "solo_ratio", "date_ratio", "friend_ratio",
    "dominant_purpose", "avg_visit_nth",
    # 집계 C (블로그 리뷰)
    "blog_review_corpus", "blog_avg_image_count",
]

MENU_COLS = [
    "place_id", "menu_name", "menu_tag", "description", "price", "price_raw",
]

VISITOR_REVIEW_COLS = [
    "place_id",
    "visit_date", "visit_time_of_day", "visit_nth",
    "reservation", "wait_time", "visit_purpose", "companion_type",
    "auth_method", "review_text", "selected_keyword",
    "additional_keyword_count", "reaction_count",
]

BLOG_REVIEW_COLS = [
    "place_id", "post_title", "post_body", "post_date", "image_count",
]


# ── 카페 단위 처리 ────────────────────────────────────────────────────────────

def process_cafe(
    cafe_dir: Path,
) -> tuple[dict, list[dict], list[dict], list[dict]] | None:
    texts_dir = cafe_dir / "texts"
    if not texts_dir.exists():
        return None

    cafe_name = cafe_dir.name
    pid       = _place_id(cafe_name)

    # 파일 읽기
    home_lines   = _read(texts_dir / "home.txt")
    info_lines   = _read(texts_dir / "info.txt")
    menu_lines   = _read(texts_dir / "menu.txt")
    review_lines = _read(texts_dir / "review.txt")
    photo_lines  = _read(texts_dir / "photo.txt")

    # 파싱
    home_data, blog_reviews = parse_home(home_lines)
    info_data               = parse_info(info_lines)
    menus                   = parse_menu(menu_lines)
    review_meta, vis_reviews = parse_review(review_lines)
    photo_cats              = parse_photo(photo_lines)

    # 집계
    agg_menu  = aggregate_menus(menus)
    agg_visit = aggregate_visitor_reviews(vis_reviews)
    agg_blog  = aggregate_blog_reviews(blog_reviews)

    # place 행 조립
    place_row: dict = {"place_id": pid}
    place_row.update(home_data)

    # info.txt 우선 적용 (편의시설, 주차, SNS, 소개)
    place_row["business_description"] = info_data.get("business_description")
    place_row["parking"]              = info_data.get("parking")
    if info_data.get("sns_url"):
        place_row["sns_url"] = info_data["sns_url"]

    # 편의시설: info.txt OR home.txt (둘 중 하나라도 True면 True)
    for col in ("amenity_takeout", "amenity_wifi", "amenity_delivery",
                "amenity_group", "amenity_separate_restroom"):
        place_row[col] = info_data.get(col, False) or home_data.get(col, False)

    place_row["photo_categories"] = photo_cats

    # 키워드 집계: review.txt 기준으로 덮어쓰기 (더 완전한 소스)
    place_row.update(review_meta)

    # 집계 결과 병합
    place_row.update(agg_menu)
    place_row.update(agg_visit)
    place_row.update(agg_blog)

    # FK 주입
    menu_rows = [{"place_id": pid, **m} for m in menus]
    vr_rows   = [{"place_id": pid, **r} for r in vis_reviews]
    br_rows   = [{"place_id": pid, **r} for r in blog_reviews]

    return place_row, menu_rows, vr_rows, br_rows


# ── CSV 저장 ─────────────────────────────────────────────────────────────────

def write_csv(path: Path, cols: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    all_places: list[dict] = []
    all_menus:  list[dict] = []
    all_vr:     list[dict] = []
    all_br:     list[dict] = []

    for cafe_dir in sorted(OUTPUT_DIR.iterdir()):
        if not cafe_dir.is_dir():
            continue
        result = process_cafe(cafe_dir)
        if result is None:
            continue

        place_row, menu_rows, vr_rows, br_rows = result
        all_places.append(place_row)
        all_menus.extend(menu_rows)
        all_vr.extend(vr_rows)
        all_br.extend(br_rows)

        print(
            f"[{cafe_dir.name}] "
            f"메뉴:{len(menu_rows)}  방문리뷰:{len(vr_rows)}  블로그:{len(br_rows)}"
        )

    write_csv(DATA_DIR / "place.csv",          PLACE_COLS,          all_places)
    write_csv(DATA_DIR / "menu.csv",            MENU_COLS,           all_menus)
    write_csv(DATA_DIR / "visitor_review.csv",  VISITOR_REVIEW_COLS, all_vr)
    write_csv(DATA_DIR / "blog_review.csv",     BLOG_REVIEW_COLS,    all_br)

    print(
        f"\n[완료] place:{len(all_places)}  menu:{len(all_menus)}  "
        f"visitor_review:{len(all_vr)}  blog_review:{len(all_br)}"
    )
    print(f"저장 위치: {DATA_DIR}/")


if __name__ == "__main__":
    main()
