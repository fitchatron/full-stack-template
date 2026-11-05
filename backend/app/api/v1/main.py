from fastapi import APIRouter

from app.api.v1.routes import auth, roles, users
from app.core.config import settings

v1 = APIRouter(prefix=settings.API_V1_STR)
v1.include_router(auth.router)
v1.include_router(roles.router)
v1.include_router(users.router)
