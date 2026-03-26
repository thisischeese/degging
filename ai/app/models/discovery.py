from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel


class DiscoveryRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        },
    )

    user_id: UUID = Field(..., description="User UUID")


class DiscoveryResponse(RootModel[dict[str, int]]):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "123e4567-e89b-12d3-a456-426614174001": 1,
                "123e4567-e89b-12d3-a456-426614174002": 2,
            }
        }
    )

    root: dict[str, int] = Field(
        default_factory=dict,
        description="Recommended cafe UUID to rank mapping",
    )
