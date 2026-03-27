"""Project constants and shared vocabulary."""

from __future__ import annotations

SURVEY_MENU_COLUMN = (
    "3. 최근 먹었던 디저트 3가지를 적어 주세요. "
    "(ex: 두쫀쿠, 소금빵, 쫀득빵, 수건케이크, 마카롱, 붕어빵, 단팥빵, 파지약과) "
)
SURVEY_MOOD_COLUMN = "6. 평소 좋아하는 카페 분위기는 무엇인가요? (2개까지 선택 가능)"
SURVEY_CONTACT_COLUMN = "기프티콘 전송을 위한 연락처(하이픈(-) 포함)를 작성해주세요(예시 010-1234-5678)"

MOOD_VOCAB = [
    "우드톤/따뜻함",
    "식물원/플랜테리어",
    "힙한",
    "조용한/차분한",
    "탁트인/뷰 좋은",
]
MOOD_TO_INDEX = {mood: index for index, mood in enumerate(MOOD_VOCAB)}

PAD_MENU = "__PAD_MENU__"
PAD_MOOD = "__PAD_MOOD__"
SYNTHETIC_SOURCE = "synthetic_preference"

WEEKDAY_KEYS = [
    "mon_hours",
    "tues_hours",
    "wed_hours",
    "thur_hours",
    "fri_hours",
]
WEEKEND_KEYS = ["sat_hours", "sun_hours"]
ALL_DAY_KEYS = WEEKDAY_KEYS + WEEKEND_KEYS

USER_PROFILE_COLUMNS = [
    "user_id",
    "nickname",
    "email",
    "preferred_menus",
    "preferred_cafe_ids",
    "mood_tags",
]

CAFE_PROFILE_COLUMNS = [
    "cafe_id",
    "name",
    "cafe_intro",
    "menu_text",
    "menu_price_stats",
    "review_text",
    "review_rating_stats",
    "business_hour_features",
]

INTERACTION_PAIR_COLUMNS = [
    "user_id",
    "cafe_id",
    "label",
    "pref_rank",
    "source",
]

USER_NESTED_COLUMNS = ["preferred_menus", "preferred_cafe_ids", "mood_tags"]
CAFE_NESTED_COLUMNS = ["menu_price_stats", "review_rating_stats", "business_hour_features"]
