from enum import StrEnum, auto
from pathlib import Path
from typing import Literal
from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.schemas.api import HTTPExceptionSchema

# backend/app/core/config.py -> repo root is two levels up from backend/
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    FASTAPI_ENV: Literal["development"] | None = None
    PROJECT_NAME: str

    DATABASE_URL: str

    # sql alchemy database pool size
    SQLALCHEMY_DATABASE_POOL_SIZE: int = 15

    # sql alchemy pessimistic disconnect handling using pool pre ping
    SQLALCHEMY_POOL_PRE_PING: bool = True

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    EMAIL_TEST_USER: EmailStr = "test@example.com"
    EMAIL_TEST_USER_PASSWORD: str = "password"

    DEFAULT_FAKER_SEED: int = 1234

    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    HTTP_EXCEPTION_RESPONSES_SET: dict = {
        "get": {
            401: {"model": HTTPExceptionSchema},
            403: {"model": HTTPExceptionSchema},
            404: {"model": HTTPExceptionSchema},
            500: {"model": HTTPExceptionSchema},
        },
        "get_all": {
            400: {"model": HTTPExceptionSchema},
            401: {"model": HTTPExceptionSchema},
            403: {"model": HTTPExceptionSchema},
            500: {"model": HTTPExceptionSchema},
        },
        "post": {
            400: {"model": HTTPExceptionSchema},
            401: {"model": HTTPExceptionSchema},
            403: {"model": HTTPExceptionSchema},
            500: {"model": HTTPExceptionSchema},
        },
        "put": {
            400: {"model": HTTPExceptionSchema},
            401: {"model": HTTPExceptionSchema},
            403: {"model": HTTPExceptionSchema},
            404: {"model": HTTPExceptionSchema},
            500: {"model": HTTPExceptionSchema},
        },
        "delete": {
            400: {"model": HTTPExceptionSchema},
            401: {"model": HTTPExceptionSchema},
            403: {"model": HTTPExceptionSchema},
            404: {"model": HTTPExceptionSchema},
            500: {"model": HTTPExceptionSchema},
        },
        "patch": {
            400: {"model": HTTPExceptionSchema},
            401: {"model": HTTPExceptionSchema},
            403: {"model": HTTPExceptionSchema},
            404: {"model": HTTPExceptionSchema},
            500: {"model": HTTPExceptionSchema},
        },
    }


settings = Settings()  # type: ignore # ty: ignore[unused-ignore-comment]
