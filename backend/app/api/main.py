from fastapi import APIRouter

from app.api.routes import items, auth
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(items.router)
api_router.include_router(auth.router)

if settings.FASTAPI_ENV == "development":

    @api_router.get("/")
    def read_root():
        return {"Hello": "World"}
