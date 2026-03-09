# CSV 설계 문서 — Two Tower 모델 Item Side

## 목적

크롤링한 txt 파일(home / menu / review / photo / info)로부터
**카페(Item) 단위의 피처**를 추출해 Two Tower 모델의 Item Tower 학습에 사용한다.
User Side는 별도 서비스에서 제공하므로 이 설계의 모든 데이터는 Item Side 전용이다.

---

## 파일 구성 (4개)

```
place.csv              ← Item Tower 최종 입력 테이블 (카페당 1행)
 ├─ menu.csv           ← 메뉴 원본 (place_id FK, 집계 후 place.csv에 반영)
 ├─ visitor_review.csv ← 방문자 리뷰 원본 (place_id FK, 집계 후 place.csv에 반영)
 └─ blog_review.csv    ← 블로그 리뷰 원본 (place_id FK, 집계 후 place.csv에 반영)
```

`menu.csv`, `visitor_review.csv`, `blog_review.csv`는 원본 보존용이자
**집계 스텝의 입력 소스**이다. Item Tower는 `place.csv` 단일 테이블만 사용한다.

---

## 1. `place.csv` — Item Tower 최종 입력

카페 1개당 1행. 정적 피처 + 3종 집계 결과를 모두 포함.

### 1-1. 정적 피처 (home.txt / info.txt)

| 컬럼 | 타입 | 출처 | 비고 |
|------|------|------|------|
| `place_id` | str | 디렉토리명 → UUID v5 | 고유 식별자 |
| `place_name` | str | home/info | 매장명 |
| `category` | str | home | "베이커리" |
| `address` | str | home | 전체 주소 |
| `district` | str | address 파싱 | "강남구" |
| `nearby_station` | str | home | "역삼역 1번 출구" |
| `station_distance_m` | int | home | 428 |
| `phone` | str | home | 전화번호 |
| `sns_url` | str | home/info | 인스타그램 URL |
| `business_description` | str | info | 브랜드 소개 문장 |
| `weekday_hours` | str | blog 본문 파싱 | "08:00-22:00" |
| `weekend_hours` | str | blog 본문 파싱 | "09:00-17:00" |
| `parking` | str | info | "주차 불가" |
| `amenity_takeout` | bool | info | 포장 가능 여부 |
| `amenity_wifi` | bool | info | 무선 인터넷 |
| `amenity_delivery` | bool | info | 배달 가능 |
| `amenity_group` | bool | info | 단체 이용 가능 |
| `amenity_separate_restroom` | bool | info | 남/녀 화장실 구분 |
| `visitor_review_count` | int | home | 399 |
| `blog_review_count` | int | home | 124 |
| `image_count` | int | home | 999 ("999+" → 999) |
| `photo_categories` | str | photo | "내부,외부,음식·음료,메뉴판,..." |

### 1-2. 키워드 집계 피처 (review.txt)

| 컬럼 | 타입 | 출처 |
|------|------|------|
| `kw_bread_tasty` | int | "빵이 맛있어요" 선택 수 |
| `kw_coffee_tasty` | int | "커피가 맛있어요" 선택 수 |
| `kw_clean` | int | "매장이 청결해요" 선택 수 |
| `kw_interior` | int | "인테리어가 멋져요" 선택 수 |
| `kw_unique_menu` | int | "특별한 메뉴가 있어요" 선택 수 |
| `menu_tag_distribution` | JSON str | review.txt 메뉴 태그 전체 분포 (예: `{"커피":23,"빨미까레":14,"라떼":9,...}`) |
| `feature_tag_distribution` | JSON str | review.txt 특징 태그 전체 분포 (예: `{"맛":104,"만족도":68,"서비스":12,...}`) |

> **주의**: 기존 설계에서 Top 2만 저장하던 방식을 전체 분포 JSON으로 교체.

---

### 1-3. 메뉴 집계 피처 — `menu.csv` → `place.csv` [집계 스텝 A]

**집계 규칙**:
- `menu.csv`에서 동일 `place_id`를 가진 모든 행을 읽어 집계
- `place.csv`에 아래 컬럼으로 반영

| 컬럼 | 타입 | 집계 방법 |
|------|------|-----------|
| `menu_count` | int | 메뉴 행 수 |
| `price_min` | int | 가격 최솟값 (None 제외) |
| `price_max` | int | 가격 최댓값 (None 제외) |
| `price_avg` | float | 가격 평균 (None 제외, 소수점 1자리) |
| `has_signature_menu` | bool | tag="대표" 행 존재 여부 |
| `menu_names_concat` | str | 전체 메뉴명을 공백으로 join (NLP 입력용) |
| `menu_desc_concat` | str | 전체 메뉴 설명문을 공백으로 join (NLP 입력용) |

---

### 1-4. 방문자 리뷰 텍스트·맥락 집계 — `visitor_review.csv` → `place.csv` [집계 스텝 B]

**집계 규칙**:
- `visitor_review.csv`에서 동일 `place_id`를 가진 모든 행을 읽어 집계
- `place.csv`에 아래 컬럼으로 반영

#### 텍스트 집계

| 컬럼 | 타입 | 집계 방법 |
|------|------|-----------|
| `visitor_review_corpus` | str | 모든 `review_text`를 `\n---\n`으로 join (NLP 임베딩 입력용) |

> `visitor_review_corpus`는 KoSimCSE 등 한국어 문장 임베딩 모델에 입력해
> 카페별 텍스트 임베딩 벡터 1개를 생성한다.
> 텍스트가 너무 길면 리뷰별 임베딩 평균(mean pooling)을 사용한다.

#### 방문 맥락 집계

| 컬럼 | 타입 | 집계 방법 |
|------|------|-----------|
| `dominant_visit_time` | str | 가장 많은 `visit_time_of_day` 값 (최빈값) |
| `morning_ratio` | float | 아침 방문 비율 (0~1) |
| `lunch_ratio` | float | 점심 방문 비율 |
| `evening_ratio` | float | 저녁 방문 비율 |
| `dominant_companion` | str | 가장 많은 `companion_type` 최빈값 |
| `solo_ratio` | float | 혼자 방문 비율 |
| `date_ratio` | float | 연인·배우자 방문 비율 |
| `friend_ratio` | float | 친구 방문 비율 |
| `dominant_purpose` | str | 가장 많은 `visit_purpose` 최빈값 |
| `avg_visit_nth` | float | 평균 방문 차수 (단골 지표) |

---

### 1-5. 블로그 리뷰 텍스트 집계 — `blog_review.csv` → `place.csv` [집계 스텝 C]

**집계 규칙**:
- `blog_review.csv`에서 동일 `place_id`를 가진 모든 행을 읽어 집계

| 컬럼 | 타입 | 집계 방법 |
|------|------|-----------|
| `blog_review_corpus` | str | 모든 `post_body`를 `\n---\n`으로 join (NLP 임베딩 입력용) |
| `blog_avg_image_count` | float | 블로그 포스트 첨부 이미지 수 평균 |

---

## 2. `menu.csv` — 메뉴 원본 (집계 스텝 A의 소스)

카페 1개당 N행. `place.csv`로 집계 후 Item Tower 입력에는 미사용.

| 컬럼 | 타입 | 출처 |
|------|------|------|
| `place_id` | str | 장소 FK |
| `menu_name` | str | menu.txt |
| `menu_tag` | str | "대표", "best", "new" 등 |
| `description` | str | 메뉴 설명 문장 |
| `price` | int\|None | 원 단위 정수 (없으면 None) |
| `price_raw` | str | "5,500원" 원본 문자열 |

---

## 3. `visitor_review.csv` — 방문자 리뷰 원본 (집계 스텝 B의 소스)

리뷰 1건당 1행. 리뷰어 개인 통계는 User Side 피처이므로 제외.

| 컬럼 | 타입 | 출처 |
|------|------|------|
| `place_id` | str | 장소 FK |
| `visit_date` | str | "2025-12-18" |
| `visit_time_of_day` | str | "아침" / "점심" / "저녁" |
| `visit_nth` | int | N번째 방문 |
| `reservation` | bool | 예약 여부 |
| `wait_time` | str | "바로 입장" / "10분 이내" 등 |
| `visit_purpose` | str | "일상" / "데이트" / "친목" 등 |
| `companion_type` | str | "혼자" / "연인·배우자" / "친구" 등 |
| `auth_method` | str | "영수증" / "결제내역" 등 |
| `review_text` | str | 리뷰 본문 |
| `selected_keyword` | str | "빵이 맛있어요" 등 선택된 키워드 |
| `additional_keyword_count` | int | "+3" 형태에서 파싱한 추가 키워드 수 |
| `reaction_count` | int | 공감 수 |

> **제거된 컬럼** (User Side 피처): `reviewer_id`, `reviewer_review_count`,
> `reviewer_photo_count`, `reviewer_follower_count`

---

## 4. `blog_review.csv` — 블로그 리뷰 원본 (집계 스텝 C의 소스)

블로그 포스트 1건당 1행.

| 컬럼 | 타입 | 출처 |
|------|------|------|
| `place_id` | str | 장소 FK |
| `post_title` | str | 블로그 포스트 제목 |
| `post_body` | str | 전체 본문 |
| `post_date` | str | "2024-08-13" |
| `image_count` | int | 첨부 이미지 수 |

> `blogger_id`는 User 식별자이므로 Item 피처에서 제외.

---

## 집계 파이프라인 전체 흐름

```
[파싱 단계]
home.txt  ──────────────────────────────────────────┐
info.txt  ───────────────────────────────────────────┼──► place.csv (정적 피처)
review.txt (키워드/태그 집계 부분) ──────────────────┘

menu.txt  ──────────────────► menu.csv
                                  │
                    [집계 스텝 A] │ menu_count, price_min/max/avg,
                                  │ has_signature_menu,
                                  │ menu_names_concat, menu_desc_concat
                                  ▼
review.txt (개별 리뷰 부분) ─► visitor_review.csv
                                  │
                    [집계 스텝 B] │ visitor_review_corpus (텍스트 join)
                                  │ dominant_visit_time, morning/lunch/evening_ratio
                                  │ dominant_companion, solo/date/friend_ratio
                                  │ dominant_purpose, avg_visit_nth
                                  ▼
home.txt (블로그 리뷰 부분) ─► blog_review.csv
                                  │
                    [집계 스텝 C] │ blog_review_corpus (텍스트 join)
                                  │ blog_avg_image_count
                                  ▼
                            place.csv (집계 컬럼 병합)
                                  │
                                  ▼
                         [Item Tower 입력]
                       정형 피처 → dense/sparse 벡터
                       *_corpus → KoSimCSE 텍스트 임베딩
                       최종 item embedding 1개 / 카페
```

---

## 파싱 규칙 요약

### home.txt
- 1~18번 라인(공통 헤더/내비) 스킵
- 주소: "서울 ..." 패턴
- 접근성: "역삼역 N번 출구에서 Xm" 패턴
- 영업시간: "XX:00에 영업 종료" 패턴
- 전화번호: 숫자-숫자 패턴
- 홈페이지: "http" 시작 라인
- 편의시설: "포장, 무선 인터넷, ..." 콤마 구분 라인
- 키워드 집계: `"..."` 라인 + 다음 라인 숫자
- 블로그 리뷰 블록: 닉네임 → 제목 → 본문 → `XX.XX.XX.요일` 날짜 패턴 → 이미지 수

### review.txt
- 키워드 집계 블록: `"..."` + 숫자 패턴
- 메뉴 태그: `텍스트숫자` 패턴 (예: `커피23`)
- 특징 태그: 동일 패턴, "메뉴" 섹션 이후 "특징" 섹션
- 방문자 리뷰 반복 블록:
  - 닉네임 (리뷰수/사진수/팔로워수 라인 바로 앞)
  - 방문 맥락: `"아침에 방문예약 없이 이용대기 시간 바로 입장데이트연인・배우자"` 형태 → 분리 파싱
  - 본문 텍스트 (다음 리뷰 블록 시작 전까지)
  - 선택 키워드: "빵이 맛있어요" 등 + `+N` 추가 수
  - 방문일: `YY.MM.DD.요일` 패턴
  - 방문 차수: `N번째 방문`
  - 인증 수단: "영수증" / "결제내역"

### menu.txt
- db.py의 `parse_menu_txt()` 로직 재사용
- 태그(대표/best/new) → `menu_tag` 컬럼에 기록 (기존엔 skip)
- 설명문(50자 초과) → `description` 컬럼에 기록 (기존엔 skip)
