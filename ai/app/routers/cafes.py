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
    summary="카페 크롤링 실행",
    description=(
        "최상위 JSON 배열 형태의 `{cafeId, name}` 목록을 받아 각 카페 정보를 실시간으로 "
        "크롤링하고, 이미지를 S3에 업로드한 뒤 정제된 응답을 반환합니다."
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
