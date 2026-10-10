import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination

from app.api.main import api_router
from app.core.config import settings
from app.core.logging import request_id_ctx, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

# only trust inbound request ids that can't inject anything into log lines
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,64}$")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """
    Tag the request with an id, write the access log line, and turn unhandled
    exceptions into a logged 500
    """
    inbound_id = request.headers.get("X-Request-ID", "")
    request_id = (
        inbound_id if REQUEST_ID_PATTERN.match(inbound_id) else uuid.uuid4().hex
    )
    token = request_id_ctx.set(request_id)
    start = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled error on %s %s", request.method, request.url.path
            )
            response = JSONResponse(
                status_code=500, content={"detail": "Internal server error"}
            )
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_ctx.reset(token)


app.include_router(api_router, prefix=settings.API_V1_STR)

# add pagination
add_pagination(app)
