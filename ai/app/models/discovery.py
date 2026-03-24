from uuid import UUID

from pydantic import BaseModel, Field


class DiscoveryRequest(BaseModel):
    user_id: UUID = Field(..., description="사용자 UUID")


class DiscoveryResponse(BaseModel):
    user_id: UUID
    cafe_ids: list[UUID] = Field(
        ...,
        description="취향 유사도 순으로 정렬된 카페 UUID 목록 (최대 100개)",
    )
    total: int = Field(..., description="반환된 카페 수")
