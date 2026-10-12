from fastapi import APIRouter

from app.api.health import health
from app.api.v1.main import v1

api_router = APIRouter()
api_router.include_router(v1)
api_router.include_router(health)
