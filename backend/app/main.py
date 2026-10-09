from fastapi import FastAPI
from fastapi_pagination import add_pagination

from app.api.main import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)
# add pagination
add_pagination(app)
app.include_router(api_router, prefix=settings.API_V1_STR)
