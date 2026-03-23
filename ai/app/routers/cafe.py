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
    summary="Preprocess a cafe query",
    description=(
        "Normalize the query text and return the current encoder and menu extraction "
        "results. The endpoint is deprecated in favor of /ai/map/search."
    ),
)
async def query_preprocess(
    request: QueryPreprocessRequest,
    service: QueryPreprocessService = Depends(get_query_preprocess_service),
) -> QueryPreprocessResponse:
    data = await service.preprocess_query(request.query, request.user_id)
    return QueryPreprocessResponse(data=data)
