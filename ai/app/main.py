import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.metrics import render_metrics
from app.routers import ai_router
from app.db.mongodb import connect_mongodb, close_mongodb
from app.db.postgresql import connect_postgresql, close_postgresql

logger = logging.getLogger("uvicorn.error")
MAX_LOG_BODY_CHARS = 1000


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_mongodb()
    await connect_postgresql()
    yield
    await close_mongodb()
    await close_postgresql()


app = FastAPI(
    title="Cafe AI Service",
    description="카페 추천/검색 AI 서비스 (Discovery & Map)",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ai_router)


def format_request_body(body: bytes) -> str:
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return "<empty>"
    if len(text) > MAX_LOG_BODY_CHARS:
        return f"{text[:MAX_LOG_BODY_CHARS]}...(truncated)"
    return text


@app.exception_handler(RequestValidationError)
async def validation_exception_logging_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.warning(
        "Request validation failed: method=%s path=%s errors=%s body=%s",
        request.method,
        request.url.path,
        exc.errors(),
        format_request_body(body),
    )
    return await request_validation_exception_handler(request, exc)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    if not settings.prometheus_metrics_enabled:
        return Response(status_code=404)
    return render_metrics()
