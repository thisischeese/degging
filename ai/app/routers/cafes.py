import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.cafe_crawling import CafeCrawlingRequest, CafeCrawlingResponse
from app.services.cafe_crawling_service import (
    CafeCrawlingService,
    CafeCrawlingSourceError,
)

router = APIRouter(prefix="/cafes", tags=["cafes"])
logger = logging.getLogger("uvicorn.error")


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
    request_items = request.root
    logger.info(
        "Cafe crawling request received: count=%s items=%s",
        len(request_items),
        [{"cafeId": item.cafeId, "name": item.name} for item in request_items[:3]],
    )
    try:
        response = await service.crawl_cafes(request_items)
        logger.info(
            "Cafe crawling request completed: requested=%s returned=%s missing=%s",
            len(request_items),
            response.total,
            len(response.missing_cafe_ids),
        )
        return response
    except CafeCrawlingSourceError as exc:
        logger.exception(
            "Cafe crawling source error: requested=%s items=%s",
            len(request_items),
            [{"cafeId": item.cafeId, "name": item.name} for item in request_items[:3]],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception(
            "Cafe crawling unexpected error: requested=%s items=%s",
            len(request_items),
            [{"cafeId": item.cafeId, "name": item.name} for item in request_items[:3]],
        )
        raise
