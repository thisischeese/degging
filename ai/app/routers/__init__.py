from fastapi import APIRouter

from app.routers.cafe import router as cafe_router
from app.routers.discovery import router as discovery_router
from app.routers.map import router as map_router

ai_router = APIRouter(prefix="/ai")
ai_router.include_router(cafe_router)
ai_router.include_router(discovery_router)
ai_router.include_router(map_router)
