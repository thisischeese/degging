from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class QueryPreprocessRequest(BaseModel):
    query: str = Field(..., description="전처리할 사용자 질의 문자열")
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
    original_query: str = Field(..., description="trim 처리된 원본 사용자 질의")
    vector: list[float] = Field(
        default_factory=list,
        description="Encoder 미연동 상태에서는 빈 배열을 반환하는 질의 벡터",
    )
    dimensions: int = Field(
        ...,
        description="벡터 차원 수. Encoder 미연동 상태에서는 0",
    )
    extracted_menus: list[str] = Field(
        default_factory=list,
        description="NER 미연동 상태에서는 빈 배열을 반환하는 추출 메뉴 목록",
    )
    menu_count: int = Field(
        ...,
        description="추출된 메뉴 수. NER 미연동 상태에서는 0",
    )


class QueryPreprocessResponse(BaseModel):
    status: Literal["success"] = Field(
        default="success",
        description="요청 성공 상태",
    )
    data: QueryPreprocessData
