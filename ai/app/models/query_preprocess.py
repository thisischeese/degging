from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class QueryPreprocessRequest(BaseModel):
    query: str = Field(..., description="전처리할 검색어")
    user_id: UUID = Field(..., description="사용자 UUID")

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
    original_query: str = Field(..., description="정규화된 검색어")
    vector: list[float] = Field(
        default_factory=list,
        description="인코딩된 검색어 벡터",
    )
    dimensions: int = Field(
        ...,
        description="검색어 벡터 차원 수",
    )
    extracted_menus: dict[str, int] = Field(
        default_factory=dict,
        description="추출된 메뉴 ID와 등장 횟수를 매핑한 결과",
    )


class QueryPreprocessResponse(BaseModel):
    status: Literal["success"] = Field(
        default="success",
        description="요청 처리 상태",
    )
    data: QueryPreprocessData
