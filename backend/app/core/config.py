from enum import StrEnum, auto
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

    DATABASE_URL: str

    # sql alchemy database pool size
    SQLALCHEMY_DATABASE_POOL_SIZE: int = 15

    # sql alchemy pessimistic disconnect handling using pool pre ping
    SQLALCHEMY_POOL_PRE_PING: bool = True

    class PERMISSIONS(StrEnum):
        @staticmethod
        def _generate_next_value_(
            name: str, start: int, count: int, last_values: list
        ) -> str:
            verb, _, resource = name.lower().partition("__")
            return (
                f"{verb.replace('asterisk', '*')}:{resource.replace('asterisk', '*')}"
            )

        def get_action_resource(self) -> tuple[str, str]:
            verb, _, resource = self.name.lower().partition("__")
            return verb.replace("asterisk", "*"), resource.replace("asterisk", "*")

        ASTERISK__ASTERISK = auto()
        CREATE__ASTERISK = auto()

        CREATE__USERS = auto()
        READ__USERS = auto()
        UPDATE__USERS = auto()
        DELETE__USERS = auto()

        CREATE__PERMISSIONS = auto()
        READ__PERMISSIONS = auto()
        UPDATE__PERMISSIONS = auto()
        DELETE__PERMISSIONS = auto()

        CREATE__ROLES = auto()
        READ__ROLES = auto()
        UPDATE__ROLES = auto()
        DELETE__ROLES = auto()

        CREATE__ROLE_PERMISSIONS = auto()
        READ__ROLE_PERMISSIONS = auto()
        UPDATE__ROLE_PERMISSIONS = auto()
        DELETE__ROLE_PERMISSIONS = auto()

        CREATE__USER_ROLES = auto()
        READ__USER_ROLES = auto()
        UPDATE__USER_ROLES = auto()
        DELETE__USER_ROLES = auto()


settings = Settings()  # type: ignore # ty: ignore[unused-ignore-comment]
