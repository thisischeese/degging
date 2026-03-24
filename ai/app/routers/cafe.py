from fastapi import APIRouter, Depends

from app.models.query_preprocess import (
    QueryPreprocessRequest,
    QueryPreprocessResponse,
)
from app.services.query_preprocess_service import QueryPreprocessService

router = APIRouter(prefix="/cafe", tags=["cafe"])


def get_query_preprocess_service() -> QueryPreprocessService:
    return QueryPreprocessService()


@router.post(
    "/query-preprocess",
    response_model=QueryPreprocessResponse,
    deprecated=True,
    summary="카페 검색어 전처리",
    description=(
        "입력된 검색어를 정규화하고 현재 인코더 결과와 메뉴 개체 추출 결과를 반환합니다. "
        "이 엔드포인트는 `/ai/map/search`로 대체될 예정입니다."
    ),
)
async def query_preprocess(
    request: QueryPreprocessRequest,
    service: QueryPreprocessService = Depends(get_query_preprocess_service),
) -> QueryPreprocessResponse:
    data = await service.preprocess_query(request.query, request.user_id)
    return QueryPreprocessResponse(data=data)
