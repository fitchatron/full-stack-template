import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import UTC, datetime

from app.core.config import settings

# set per request by the request context middleware in app.main
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """
    Attach the current request id to every log record
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    """
    One JSON object per line, for log collectors outside development
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging() -> None:
    """
    Configure logging once at startup. Modules log via logging.getLogger(__name__)
    and never add their own handlers.
    """
    is_dev = settings.FASTAPI_ENV == "development"

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"request_id": {"()": RequestIdFilter}},
            "formatters": {
                "text": {
                    "format": "%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s: %(message)s"
                },
                "json": {"()": JsonFormatter},
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "text" if is_dev else "json",
                    "filters": ["request_id"],
                },
            },
            "root": {"handlers": ["default"], "level": settings.LOG_LEVEL},
            "loggers": {
                # route uvicorn through the root handler so all output shares one format
                "uvicorn": {"handlers": [], "propagate": True},
                # replaced by the access log in the request context middleware
                "uvicorn.access": {"handlers": [], "propagate": False},
                # INFO here logs every SQL statement
                "sqlalchemy.engine": {"level": "WARNING"},
            },
        }
    )
