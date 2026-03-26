from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import get_mongo_db
from app.models.discovery import DiscoveryRequest, DiscoveryResponse
from app.services.discovery_service import DiscoveryService, UserPreferenceNotFoundError

router = APIRouter(prefix="/discovery", tags=["discovery"])


def get_discovery_service(
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> DiscoveryService:
    return DiscoveryService(mongo_db)


@router.post(
    "",
    response_model=DiscoveryResponse,
    summary="사용자 취향 기반 카페 추천",
    description=(
        "메인 서비스에서 전달받은 `user_id`를 기준으로 MongoDB에서 취향 벡터를 조회하고, "
        "PostgreSQL pgvector ANN 인덱스를 사용해 유사한 카페를 최대 100개까지 반환합니다."
    ),
)
async def discover(
    request: DiscoveryRequest,
    service: DiscoveryService = Depends(get_discovery_service),
) -> DiscoveryResponse:
    try:
        cafe_ids = await service.discover(request.user_id)
    except UserPreferenceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    ranked_cafes = {
        str(cafe_id): rank for rank, cafe_id in enumerate(cafe_ids, start=1)
    }

    return DiscoveryResponse(root=ranked_cafes)
