"""Data loading and preprocessing helpers for the two-tower pipeline."""

from __future__ import annotations

from collections.abc import Iterable
import hashlib
import json
from pathlib import Path
import re
import uuid

from faker import Faker
import numpy as np
import pandas as pd

from twotower.constants import (
    ALL_DAY_KEYS,
    CAFE_NESTED_COLUMNS,
    INTERACTION_PAIR_COLUMNS,
    MOOD_VOCAB,
    PAD_MENU,
    PAD_MOOD,
    SURVEY_CONTACT_COLUMN,
    SURVEY_MENU_COLUMN,
    SURVEY_MOOD_COLUMN,
    SYNTHETIC_SOURCE,
    USER_NESTED_COLUMNS,
    WEEKDAY_KEYS,
    WEEKEND_KEYS,
)


def stable_seed(value: str) -> int:
    """Create a deterministic integer seed from a string value."""
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % (2**31)


def _clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u200b", " ")).strip()


def normalize_menu_token(value: str) -> str:
    """Normalize a free-form menu string into a stable token."""
    cleaned = _clean_whitespace(value)
    cleaned = re.sub(r"[\"'`]", "", cleaned)
    cleaned = re.sub(r"[()]+", " ", cleaned)
    cleaned = re.sub(r"[|]+", " ", cleaned)
    cleaned = _clean_whitespace(cleaned)
    return cleaned


def split_multi_select(value: str) -> list[str]:
    """Split comma-separated survey values while keeping order."""
    if not isinstance(value, str):
        return []
    return [_clean_whitespace(part) for part in value.split(",") if _clean_whitespace(part)]


def extract_preferred_menus(value: str, *, size: int = 3) -> list[str]:
    """Extract at most three normalized menu preferences from survey text."""
    normalized: list[str] = []
    for part in split_multi_select(value):
        token = normalize_menu_token(part)
        if token and token not in normalized:
            normalized.append(token)
        if len(normalized) == size:
            break
    while len(normalized) < size:
        normalized.append(PAD_MENU)
    return normalized


def extract_mood_tags(value: str, *, size: int = 3) -> list[str]:
    """Map a free-form mood answer into the fixed mood vocabulary."""
    matches: list[str] = []
    pieces = split_multi_select(value)
    search_space = pieces + ([value] if isinstance(value, str) else [])
    for piece in search_space:
        for mood in MOOD_VOCAB:
            if mood in piece and mood not in matches:
                matches.append(mood)
                if len(matches) == size:
                    break
        if len(matches) == size:
            break
    while len(matches) < size:
        matches.append(PAD_MOOD)
    return matches


def _build_synthetic_identity(seed_source: str) -> tuple[str, str]:
    seed = stable_seed(seed_source)
    fake = Faker("ko_KR")
    fake.seed_instance(seed)

    nickname = re.sub(r"[^A-Za-z0-9_]", "", fake.user_name())
    if not nickname:
        nickname = f"user{seed % 100000}"

    local = re.sub(r"[^A-Za-z0-9_.-]", "", nickname.lower())
    local = local or f"user{seed % 100000}"
    email = f"{local}.{seed % 10000}@example.com"
    return nickname, email


def load_survey_dataframe(csv_path: Path) -> pd.DataFrame:
    """Load the Google Form CSV with UTF-8 BOM support."""
    return pd.read_csv(csv_path, encoding="utf-8-sig")


def build_user_profiles(survey_df: pd.DataFrame) -> pd.DataFrame:
    """Create user profiles with deterministic synthetic identity fields."""
    records: list[dict[str, object]] = []
    for index, row in survey_df.iterrows():
        contact = str(row.get(SURVEY_CONTACT_COLUMN, "") or "").strip()
        seed_source = contact or f"row-{index}"
        nickname, email = _build_synthetic_identity(seed_source)
        preferred_menus = extract_preferred_menus(str(row.get(SURVEY_MENU_COLUMN, "") or ""))
        mood_tags = extract_mood_tags(str(row.get(SURVEY_MOOD_COLUMN, "") or ""))
        raw_user_key = "|".join(
            [seed_source, str(row.get(SURVEY_MENU_COLUMN, "") or ""), str(row.get(SURVEY_MOOD_COLUMN, "") or "")]
        )
        records.append(
            {
                "user_id": str(uuid.uuid5(uuid.NAMESPACE_URL, raw_user_key)),
                "nickname": nickname,
                "email": email,
                "preferred_menus": preferred_menus,
                "preferred_cafe_ids": [],
                "mood_tags": mood_tags,
            }
        )
    return pd.DataFrame.from_records(records)


def _parse_minutes(value: str | None) -> tuple[int, int] | None:
    if not value or not isinstance(value, str):
        return None
    match = re.search(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", value)
    if not match:
        return None
    start_hour, start_minute, end_hour, end_minute = map(int, match.groups())
    start = start_hour * 60 + start_minute
    end = end_hour * 60 + end_minute
    if end <= start:
        return None
    return start, end


def _build_business_hour_features(hours: dict[str, str | None] | None) -> dict[str, float]:
    features = {
        "open_days_count": 0.0,
        "weekday_open_minutes": 0.0,
        "weekend_open_minutes": 0.0,
        "opens_before_09": 0.0,
        "closes_after_21": 0.0,
    }
    hours = hours or {}

    for day_key in ALL_DAY_KEYS:
        day_range = _parse_minutes(hours.get(day_key))
        is_open = 1.0 if day_range else 0.0
        features[f"{day_key}_open"] = is_open
        if not day_range:
            continue
        start_minute, end_minute = day_range
        open_minutes = float(end_minute - start_minute)
        features["open_days_count"] += 1.0
        if day_key in WEEKDAY_KEYS:
            features["weekday_open_minutes"] += open_minutes
        if day_key in WEEKEND_KEYS:
            features["weekend_open_minutes"] += open_minutes
        if start_minute < 9 * 60:
            features["opens_before_09"] = 1.0
        if end_minute >= 21 * 60:
            features["closes_after_21"] = 1.0
    return features


def _build_menu_text(menus: list[dict[str, object]]) -> str:
    chunks: list[str] = []
    for menu in menus[:20]:
        name = _clean_whitespace(str(menu.get("menu_name", "") or ""))
        description = _clean_whitespace(str(menu.get("menu_description", "") or ""))
        price = menu.get("price")
        price_text = f"가격 {int(price)}원" if isinstance(price, (int, float)) else ""
        chunk = " ".join(part for part in [name, price_text, description] if part)
        if chunk:
            chunks.append(chunk)
    return " ".join(chunks)


def _build_review_text(reviews: list[dict[str, object]]) -> str:
    texts = [
        _clean_whitespace(str(review.get("user_review", "") or ""))
        for review in reviews[:5]
        if _clean_whitespace(str(review.get("user_review", "") or ""))
    ]
    return " ".join(texts)


def _build_menu_price_stats(menus: list[dict[str, object]]) -> dict[str, float]:
    prices = [float(menu["price"]) for menu in menus if isinstance(menu.get("price"), (int, float))]
    if not prices:
        return {"menu_count": float(len(menus)), "price_min": 0.0, "price_max": 0.0, "price_mean": 0.0}
    return {
        "menu_count": float(len(menus)),
        "price_min": float(np.min(prices)),
        "price_max": float(np.max(prices)),
        "price_mean": float(np.mean(prices)),
    }


def _build_review_rating_stats(reviews: list[dict[str, object]]) -> dict[str, float]:
    ratings = [float(review["rating"]) for review in reviews if isinstance(review.get("rating"), (int, float))]
    if not ratings:
        return {"review_count": float(len(reviews)), "review_rating_mean": 0.0, "review_rating_std": 0.0}
    return {
        "review_count": float(len(reviews)),
        "review_rating_mean": float(np.mean(ratings)),
        "review_rating_std": float(np.std(ratings)),
    }


def load_crawl_items(crawl_dir: Path) -> list[dict[str, object]]:
    """Load and de-duplicate crawl items by cafe_id."""
    deduped: dict[str, dict[str, object]] = {}
    for path in sorted(crawl_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("items", []):
            cafe_id = item.get("cafe_id")
            if cafe_id:
                deduped[str(cafe_id)] = item
    return [deduped[key] for key in sorted(deduped)]


def build_cafe_profiles(items: Iterable[dict[str, object]]) -> pd.DataFrame:
    """Flatten nested crawl results into cafe_profile rows."""
    records: list[dict[str, object]] = []
    for item in items:
        cafe = item.get("cafes") or {}
        menus = list(item.get("cafe_menus") or [])
        reviews = list(item.get("cafe_reviews") or [])
        hours = dict(item.get("cafe_business_hours") or {})
        records.append(
            {
                "cafe_id": str(item.get("cafe_id") or cafe.get("cafe_id") or ""),
                "name": _clean_whitespace(str(cafe.get("name", "") or "")),
                "cafe_intro": _clean_whitespace(str(cafe.get("cafe_intro", "") or "")),
                "menu_text": _build_menu_text(menus),
                "menu_price_stats": _build_menu_price_stats(menus),
                "review_text": _build_review_text(reviews),
                "review_rating_stats": _build_review_rating_stats(reviews),
                "business_hour_features": _build_business_hour_features(hours),
            }
        )
    return pd.DataFrame.from_records(records)


def build_user_query_text(row: pd.Series) -> str:
    menus = [menu for menu in row["preferred_menus"] if menu != PAD_MENU]
    moods = [mood for mood in row["mood_tags"] if mood != PAD_MOOD]
    return " ".join(["선호메뉴", " ".join(menus), "선호분위기", " ".join(moods)]).strip()


def build_cafe_matching_text(row: pd.Series) -> str:
    return " ".join(
        [
            str(row.get("name", "") or ""),
            str(row.get("cafe_intro", "") or ""),
            str(row.get("menu_text", "") or ""),
            str(row.get("review_text", "") or ""),
        ]
    ).strip()


def assign_preferred_cafe_ids(
    user_df: pd.DataFrame,
    cafe_df: pd.DataFrame,
    *,
    encoder: object,
    top_k: int = 3,
) -> pd.DataFrame:
    """Populate preferred_cafe_ids by text similarity over cafes."""
    user_df = user_df.copy()
    cafe_df = cafe_df.copy()

    cafe_documents = cafe_df.apply(build_cafe_matching_text, axis=1).tolist()
    user_queries = user_df.apply(build_user_query_text, axis=1).tolist()

    encoder.fit(cafe_documents + user_queries)
    cafe_vectors = encoder.transform(cafe_documents)
    query_vectors = encoder.transform(user_queries)
    similarity = query_vectors @ cafe_vectors.T

    preferred_ids: list[list[str]] = []
    for row_index in range(similarity.shape[0]):
        ranked = np.argsort(-similarity[row_index])[:top_k]
        preferred_ids.append(cafe_df.iloc[ranked]["cafe_id"].tolist())

    user_df["preferred_cafe_ids"] = preferred_ids
    return user_df


def build_interaction_pairs(user_df: pd.DataFrame) -> pd.DataFrame:
    """Expand preferred cafe lists into positive-only interaction rows."""
    records: list[dict[str, object]] = []
    for _, row in user_df.iterrows():
        for pref_rank, cafe_id in enumerate(row["preferred_cafe_ids"], start=1):
            records.append(
                {
                    "user_id": row["user_id"],
                    "cafe_id": cafe_id,
                    "label": 1,
                    "pref_rank": pref_rank,
                    "source": SYNTHETIC_SOURCE,
                }
            )
    return pd.DataFrame.from_records(records, columns=INTERACTION_PAIR_COLUMNS)


def build_user_splits(
    user_ids: list[str],
    *,
    train_ratio: float,
    val_ratio: float,
    random_seed: int,
) -> pd.DataFrame:
    """Assign train/val/test splits by user_id."""
    rng = np.random.default_rng(random_seed)
    shuffled = list(user_ids)
    rng.shuffle(shuffled)

    total = len(shuffled)
    train_end = max(1, int(total * train_ratio))
    val_end = min(total, train_end + max(1, int(total * val_ratio)))
    if val_end >= total:
        val_end = max(train_end, total - 1)

    split_map: dict[str, str] = {}
    for position, user_id in enumerate(shuffled):
        if position < train_end:
            split_map[user_id] = "train"
        elif position < val_end:
            split_map[user_id] = "val"
        else:
            split_map[user_id] = "test"

    return pd.DataFrame({"user_id": user_ids, "split": [split_map[user_id] for user_id in user_ids]})


def serialize_nested_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Serialize list/dict columns to JSON strings for Parquet export."""
    serialized = df.copy()
    for column in columns:
        serialized[column] = serialized[column].map(lambda value: json.dumps(value, ensure_ascii=False))
    return serialized


def deserialize_nested_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Deserialize list/dict columns that were persisted as JSON strings."""
    deserialized = df.copy()
    for column in columns:
        deserialized[column] = deserialized[column].map(json.loads)
    return deserialized


def save_prepared_artifacts(
    *,
    user_df: pd.DataFrame,
    cafe_df: pd.DataFrame,
    interaction_df: pd.DataFrame,
    split_df: pd.DataFrame,
    user_path: Path,
    cafe_path: Path,
    interaction_path: Path,
    split_path: Path,
) -> None:
    serialize_nested_columns(user_df, USER_NESTED_COLUMNS).to_parquet(user_path, index=False)
    serialize_nested_columns(cafe_df, CAFE_NESTED_COLUMNS).to_parquet(cafe_path, index=False)
    interaction_df.to_parquet(interaction_path, index=False)
    split_df.to_parquet(split_path, index=False)


def load_prepared_artifacts(
    *,
    user_path: Path,
    cafe_path: Path,
    interaction_path: Path,
    split_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    user_df = deserialize_nested_columns(pd.read_parquet(user_path), USER_NESTED_COLUMNS)
    cafe_df = deserialize_nested_columns(pd.read_parquet(cafe_path), CAFE_NESTED_COLUMNS)
    interaction_df = pd.read_parquet(interaction_path)
    split_df = pd.read_parquet(split_path)
    return user_df, cafe_df, interaction_df, split_df
