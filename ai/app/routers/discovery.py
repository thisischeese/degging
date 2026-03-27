from fastapi import APIRouter, Depends, HTTPException, status

from app.models.discovery import DiscoveryRequest, DiscoveryResponse
from app.services.discovery_service import DiscoveryService, UserPreferenceNotFoundError

router = APIRouter(prefix="/discovery", tags=["discovery"])


def get_discovery_service() -> DiscoveryService:
    return DiscoveryService()


@router.post(
    "",
    response_model=DiscoveryResponse,
    summary="Recommend cafes from a user's preference vector",
    description=(
        "Load the user's `preference_vector` from PostgreSQL `user_preference`, "
        "then return up to 100 cafes from PostgreSQL `cafes.cafe_vector` ordered by "
        "cosine-distance ANN ranking."
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
