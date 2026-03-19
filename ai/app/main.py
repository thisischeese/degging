from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import ai_router
from app.db.mongodb import connect_mongodb, close_mongodb
from app.db.postgresql import connect_postgresql, close_postgresql


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


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
