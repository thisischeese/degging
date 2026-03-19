from fastapi import APIRouter
from app.routers.discovery import router as discovery_router

ai_router = APIRouter(prefix="/ai")
ai_router.include_router(discovery_router)