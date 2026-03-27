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
    summary="지도용 카페 검색",
    description=(
        "사용자 검색어를 전처리하고 주변 카페 후보를 찾은 뒤, "
        "정렬된 카페 목록과 추출된 메뉴 ID를 반환합니다."
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
