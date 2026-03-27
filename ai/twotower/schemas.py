"""Data contracts for the positive-only two-tower pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class UserProfile:
    user_id: str
    nickname: str
    email: str
    preferred_menus: list[str]
    preferred_cafe_ids: list[str]
    mood_tags: list[str]


@dataclass(slots=True)
class CafeProfile:
    cafe_id: str
    name: str
    cafe_intro: str
    menu_text: str
    menu_price_stats: dict[str, float | int | None]
    review_text: str
    review_rating_stats: dict[str, float | int | None]
    business_hour_features: dict[str, float | int | None]


@dataclass(slots=True)
class InteractionPair:
    user_id: str
    cafe_id: str
    label: int
    pref_rank: int
    source: str = "synthetic_preference"
