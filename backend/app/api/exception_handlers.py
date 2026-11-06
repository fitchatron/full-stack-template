import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.exception import AppError, ConflictError, UnprocessableContentError

logger = logging.getLogger(__name__)

# client-facing wording for unique constraints, named by the convention in app.core.db
UNIQUE_CONSTRAINT_MESSAGES = {
    "uq__users__email": "Email already in use",
    "uq__users__username": "Username already in use",
    "uq__roles__name": "Name already in use",
    "uq__permissions__action_resource": "Permission already exists",
}

HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "unprocessable_content",
    503: "service_unavailable",
}


def error_body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def translate_integrity_error(exception: IntegrityError, constraint: str) -> AppError:
    """
    Map a Postgres SQLSTATE to a domain error. Anything unrecognised stays a 500.
    """
    match getattr(exception.orig, "sqlstate", None):
        case "23505":  # unique_violation
            return ConflictError(
                UNIQUE_CONSTRAINT_MESSAGES.get(constraint, "Resource already exists")
            )
        case "23P01":  # exclusion_violation
            return ConflictError("Resource conflicts with an existing record")
        case "23503":  # foreign_key_violation
            return UnprocessableContentError("Referenced resource does not exist")
        case "23502" | "23514":  # not_null_violation or check_violation
            return UnprocessableContentError("Invalid data")
        case _:
            return AppError("A database integrity constraint was violated")


async def app_error_handler(request: Request, exception: AppError) -> JSONResponse:
    """
    Domain errors are expected outcomes, so log the reason without a traceback.
    A 5xx is a real fault, so it logs at ERROR with one.
    """
    is_server_error = exception.status_code >= 500
    logger.log(
        logging.ERROR if is_server_error else logging.INFO,
        "%s %s -> %s: %s",
        request.method,
        request.url.path,
        exception.status_code,
        exception,
        exc_info=exception if is_server_error else None,
    )
    return JSONResponse(
        status_code=exception.status_code,
        content=error_body(exception.code, exception.message, exception.details),
        headers=exception.headers,
    )


async def integrity_error_handler(
    request: Request, exception: IntegrityError
) -> JSONResponse:
    """
    Translate database integrity errors into client errors where possible
    """
    constraint = (
        getattr(getattr(exception.orig, "diag", None), "constraint_name", None) or ""
    )
    app_exception = translate_integrity_error(exception, constraint)

    is_server_error = app_exception.status_code >= 500
    logger.log(
        logging.ERROR if is_server_error else logging.INFO,
        "%s %s -> %s: constraint %s violated",
        request.method,
        request.url.path,
        app_exception.status_code,
        constraint or "unknown",
        exc_info=exception if is_server_error else None,
    )
    return JSONResponse(
        status_code=app_exception.status_code,
        content=error_body(
            app_exception.code, app_exception.message, app_exception.details
        ),
    )


async def http_exception_handler(
    _: Request, exception: StarletteHTTPException
) -> JSONResponse:
    """
    Framework errors (unknown routes, missing tokens) use the same body as domain errors
    """
    return JSONResponse(
        status_code=exception.status_code,
        content=error_body(
            HTTP_ERROR_CODES.get(exception.status_code, "http_error"),
            str(exception.detail),
        ),
        headers=exception.headers,
    )


async def validation_error_handler(
    _: Request, exception: RequestValidationError
) -> JSONResponse:
    """
    jsonable_encoder is required: validators that raise ValueError leave the
    exception object in the error context, which JSONResponse can't serialize
    """
    return JSONResponse(
        status_code=422,
        content=error_body(
            "validation_error",
            "Invalid request",
            {"errors": jsonable_encoder(exception.errors())},
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.exception_handler(AppError)(app_error_handler)
    app.exception_handler(IntegrityError)(integrity_error_handler)
    app.exception_handler(StarletteHTTPException)(http_exception_handler)
    app.exception_handler(RequestValidationError)(validation_error_handler)
