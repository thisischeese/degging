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
    summary="Merge cafe crawling sources",
    description=(
        "cafe.json 형태의 배열 body를 받아 데이터 크롤링 후,"
        "S3에 이미지 업로드하고 데이터 정제해 cafe_id 기준으로 병합해 반환합니다."
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
