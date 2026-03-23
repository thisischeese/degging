from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class QueryPreprocessRequest(BaseModel):
    query: str = Field(..., description="Query text to preprocess")
    user_id: UUID = Field(..., description="User UUID")

    @field_validator("query", mode="before")
    @classmethod
    def validate_query(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("query must be a string")

        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be blank")

        return stripped


class QueryPreprocessData(BaseModel):
    original_query: str = Field(..., description="Normalized query")
    vector: list[float] = Field(
        default_factory=list,
        description="Encoded query vector",
    )
    dimensions: int = Field(
        ...,
        description="Query vector dimensions",
    )
    extracted_menus: dict[str, int] = Field(
        default_factory=dict,
        description="Resolved menu ids mapped to occurrence counts",
    )


class QueryPreprocessResponse(BaseModel):
    status: Literal["success"] = Field(
        default="success",
        description="Request status",
    )
    data: QueryPreprocessData
