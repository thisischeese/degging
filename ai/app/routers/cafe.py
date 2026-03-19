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
    summary="사용자 쿼리 전처리",
    description=(
        "사용자 질의를 전처리하고 질의 벡터화 및 메뉴 추출 결과를 반환합니다. "
        "현재 encoder 및 NER 연동은 stub 상태이므로 빈 결과를 반환합니다."
    ),
)
async def query_preprocess(
    request: QueryPreprocessRequest,
    service: QueryPreprocessService = Depends(get_query_preprocess_service),
) -> QueryPreprocessResponse:
    data = await service.preprocess_query(request.query, request.user_id)
    return QueryPreprocessResponse(data=data)
