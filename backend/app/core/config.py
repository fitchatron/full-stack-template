from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> repo root is two levels up from backend/
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    FASTAPI_ENV: Literal["development"] | None = None
    PROJECT_NAME: str


settings = Settings()  # type: ignore # ty: ignore[unused-ignore-comment]
