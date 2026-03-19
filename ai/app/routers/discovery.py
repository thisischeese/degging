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
        "메인 서버로부터 user_id를 받아 MongoDB에서 취향 벡터를 조회하고, "
        "PostgreSQL pgvector ANN 인덱스로 유사 카페 최대 100개를 반환합니다."
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

    return DiscoveryResponse(
        user_id=request.user_id,
        cafe_ids=cafe_ids,
        total=len(cafe_ids),
    )