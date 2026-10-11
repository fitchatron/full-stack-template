import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import settings

LOGGER_CONFIG_FILE = Path(__file__).with_name("logger.config.json")

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

    The static config lives in logger.config.json:
    - uvicorn propagates to the root handler so all output shares one format
    - uvicorn.access is replaced by the access log in the request context middleware
    - sqlalchemy.engine stays at WARNING, since INFO logs every SQL statement
    """
    config = json.loads(LOGGER_CONFIG_FILE.read_text())

    # settings-dependent values override the file
    is_dev = settings.FASTAPI_ENV == "development"
    config["handlers"]["default"]["formatter"] = "text" if is_dev else "json"
    config["root"]["level"] = settings.LOG_LEVEL

    logging.config.dictConfig(config)
