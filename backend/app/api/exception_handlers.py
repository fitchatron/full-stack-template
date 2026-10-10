import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.utils.exception import AppError

logger = logging.getLogger(__name__)

# unique constraints follow the naming convention in app.core.db: uq__<table>__<columns>
UNIQUE_CONSTRAINT_PREFIX = "uq__"


async def app_error_handler(request: Request, exception: AppError) -> JSONResponse:
    """
    Domain errors are expected outcomes, so log the reason without a traceback
    """
    logger.info(
        "%s %s -> %s: %s",
        request.method,
        request.url.path,
        exception.status_code,
        exception,
    )
    return JSONResponse(
        status_code=exception.status_code, content={"detail": str(exception)}
    )


async def integrity_error_handler(
    request: Request, exception: IntegrityError
) -> JSONResponse:
    """
    Unique constraint violations are a client conflict (409), anything else is a 500
    """
    constraint = (
        getattr(getattr(exception.orig, "diag", None), "constraint_name", None) or ""
    )

    if not constraint.startswith(UNIQUE_CONSTRAINT_PREFIX):
        logger.exception("Integrity error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Database integrity error"},
        )

    field = constraint.split("__")[-1].replace("_", " ").capitalize()
    logger.info(
        "%s %s -> 409: unique constraint %s violated",
        request.method,
        request.url.path,
        constraint,
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": f"{field} already in use"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.exception_handler(AppError)(app_error_handler)
    app.exception_handler(IntegrityError)(integrity_error_handler)
