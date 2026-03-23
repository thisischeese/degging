from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MapSearchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mood: list[int] = Field(default_factory=list, description="Mood ids")
    user_id: UUID = Field(alias="userId", description="User UUID")
    keyword: str = Field(..., description="Search keyword")
    latitude: float = Field(..., description="User latitude")
    longitude: float = Field(..., description="User longitude")

    @field_validator("mood", mode="before")
    @classmethod
    def validate_mood(cls, value: object) -> list[int]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("mood must be a list")
        return value

    @field_validator("keyword", mode="before")
    @classmethod
    def validate_keyword(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("keyword must be a string")
        return value.strip()

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if value < -90 or value > 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if value < -180 or value > 180:
            raise ValueError("longitude must be between -180 and 180")
        return value


class MapSearchResponse(BaseModel):
    cafes: dict[str, int] = Field(
        default_factory=dict,
        description="Cafe ids mapped to 1-based ranks",
    )
    extracted_menus: dict[str, int] = Field(
        default_factory=dict,
        description="Resolved menu ids mapped to occurrence counts",
    )
