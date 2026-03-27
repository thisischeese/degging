from __future__ import annotations

import re
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_non_empty_string_list(
    value: object,
    *,
    field_name: str,
) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} must contain only strings")
        stripped = item.strip()
        if not stripped:
            raise ValueError(f"{field_name} items must be non-empty strings")
        normalized.append(stripped)
    return normalized


class OnboardingRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "nickname": "newuser01",
                "email": "newuser01@example.com",
                "favorite_menus": ["두쫀쿠", "커피", "버터떡"],
                "mood_tags": ["우드톤/따뜻한", "빛나는?", "최대3개/최소1개"],
                "cafes": [
                    "123e4567-e89b-12d3-a456-426614174001",
                    "123e4567-e89b-12d3-a456-426614174002",
                    "123e4567-e89b-12d3-a456-426614174003",
                ],
            }
        },
    )

    user_id: UUID = Field(..., description="User UUID")
    nickname: str = Field(..., description="User nickname")
    email: str = Field(..., description="User email")
    favorite_menus: list[str] = Field(..., description="1 to 3 preferred menu strings")
    mood_tags: list[str] = Field(..., description="1 to 3 mood tag strings")
    cafes: list[UUID] = Field(..., description="1 to 3 preferred cafe UUIDs")

    @field_validator("nickname", mode="before")
    @classmethod
    def validate_nickname(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("nickname must be a string")
        stripped = value.strip()
        if not stripped:
            raise ValueError("nickname must be a non-empty string")
        return stripped

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("email must be a string")
        normalized = value.strip().lower()
        if not normalized or not _EMAIL_PATTERN.match(normalized):
            raise ValueError("email must be a valid email address")
        return normalized

    @field_validator("favorite_menus", mode="before")
    @classmethod
    def validate_favorite_menus(cls, value: object) -> list[str]:
        return _validate_non_empty_string_list(value, field_name="favorite_menus")

    @field_validator("mood_tags", mode="before")
    @classmethod
    def validate_mood_tags(cls, value: object) -> list[str]:
        return _validate_non_empty_string_list(value, field_name="mood_tags")

    @field_validator("favorite_menus")
    @classmethod
    def validate_favorite_menu_count(cls, value: list[str]) -> list[str]:
        if not 1 <= len(value) <= 3:
            raise ValueError("favorite_menus must contain between 1 and 3 items")
        return value

    @field_validator("mood_tags")
    @classmethod
    def validate_mood_tag_count(cls, value: list[str]) -> list[str]:
        if not 1 <= len(value) <= 3:
            raise ValueError("mood_tags must contain between 1 and 3 items")
        return value

    @field_validator("cafes", mode="before")
    @classmethod
    def validate_cafes_is_list(cls, value: object) -> object:
        if not isinstance(value, list):
            raise ValueError("cafes must be a list")
        return value

    @field_validator("cafes")
    @classmethod
    def validate_cafe_count(cls, value: list[UUID]) -> list[UUID]:
        if not 1 <= len(value) <= 3:
            raise ValueError("cafes must contain between 1 and 3 items")
        return value


class OnboardingResponseData(BaseModel):
    user_id: UUID
    updated_at: datetime


class OnboardingResponse(BaseModel):
    status: Literal["success"]
    message: str
    data: OnboardingResponseData
