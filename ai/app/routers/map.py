from fastapi import APIRouter, Depends, HTTPException, status

from app.models.map_search import MapSearchRequest, MapSearchResponse
from app.services.map_search_service import MapSearchService
from app.services.preference_vector import UserPreferenceNotFoundError

router = APIRouter(prefix="/map", tags=["map"])


def get_map_search_service() -> MapSearchService:
    return MapSearchService()


@router.post(
    "/search",
    response_model=MapSearchResponse,
    summary="Map cafe search",
    description=(
        "Preprocesses the user keyword, ranks nearby cafes, and returns cafe "
        "rankings with resolved menu names."
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
