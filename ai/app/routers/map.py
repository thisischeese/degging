from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import get_mongo_db
from app.models.map_search import MapSearchRequest, MapSearchResponse
from app.services.discovery_service import UserPreferenceNotFoundError
from app.services.map_search_service import MapSearchService

router = APIRouter(prefix="/map", tags=["map"])


def get_map_search_service(
    mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> MapSearchService:
    return MapSearchService(mongo_db)


@router.post(
    "/search",
    response_model=MapSearchResponse,
    summary="Search cafes for map results",
    description=(
        "Preprocess the user query, resolve nearby cafe candidates, "
        "and return ranked cafes with resolved menu ids."
    ),
)
async def map_search(
    request: MapSearchRequest,
    service: MapSearchService = Depends(get_map_search_service),
) -> MapSearchResponse:
    try:
        return await service.search(request)
    except UserPreferenceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
