import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.models.discovery import DiscoveryRequest, DiscoveryResponse
from app.services.discovery_service import (
    DiscoveryService,
    RecommendedCafe,
    UserPreferenceNotFoundError,
)

router = APIRouter(prefix="/discovery", tags=["discovery"])
logger = logging.getLogger("uvicorn.error.discovery")
logger.setLevel(getattr(logging, settings.discovery_log_level.upper(), logging.DEBUG))
_UNKNOWN_CAFE_NAME = "<unnamed-cafe>"


def get_discovery_service() -> DiscoveryService:
    return DiscoveryService()


def _serialize_recommendations_for_log(
    recommended_cafes: list[RecommendedCafe],
) -> list[dict[str, str | int]]:
    return [
        {
            "rank": rank,
            "cafe_id": str(cafe.cafe_id),
            "name": cafe.name or _UNKNOWN_CAFE_NAME,
        }
        for rank, cafe in enumerate(recommended_cafes, start=1)
    ]


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
    logger.debug("discovery_request_started: user_id=%s", request.user_id)

    try:
        recommended_cafes = await service.discover(request.user_id)
    except UserPreferenceNotFoundError as exc:
        logger.warning(
            "discovery_preference_not_found: user_id=%s detail=%s",
            request.user_id,
            str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception:
        logger.exception(
            "discovery_request_failed: user_id=%s",
            request.user_id,
        )
        raise

    ranked_cafes = {
        str(cafe.cafe_id): rank
        for rank, cafe in enumerate(recommended_cafes, start=1)
    }
    logger.debug(
        "discovery_request_completed: user_id=%s recommendation_count=%s recommendations=%s",
        request.user_id,
        len(recommended_cafes),
        _serialize_recommendations_for_log(recommended_cafes),
    )

    return DiscoveryResponse(root=ranked_cafes)
