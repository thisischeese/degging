from fastapi import APIRouter, Depends, HTTPException, status

from app.models.cafe_crawling import CafeCrawlingRequest, CafeCrawlingResponse
from app.services.cafe_crawling_service import (
    CafeCrawlingService,
    CafeCrawlingSourceError,
)

router = APIRouter(prefix="/cafes", tags=["cafes"])


def get_cafe_crawling_service() -> CafeCrawlingService:
    return CafeCrawlingService()


@router.post(
    "/crawling",
    response_model=CafeCrawlingResponse,
    summary="Crawl cafes on demand",
    description=(
        "Accepts a top-level JSON array of `{cafeId, name}` items, crawls each cafe live, "
        "uploads images to S3, and returns the refined response."
    ),
)
async def cafe_crawling(
    request: CafeCrawlingRequest,
    service: CafeCrawlingService = Depends(get_cafe_crawling_service),
) -> CafeCrawlingResponse:
    try:
        return await service.crawl_cafes(request.root)
    except CafeCrawlingSourceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
