from typing import Any

from fastapi import HTTPException, status


class TokenError(Exception):
    pass


class CommunicationError(TokenError):
    pass


class InvalidToken(TokenError):
    pass


class InvalidKeys(TokenError):
    pass


class AuthError(Exception):
    pass


class NoOrderByColumnsSpecified(Exception):
    pass


class InvalidAuthorization(HTTPException):
    def __init__(self, detail: Any = None) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AppError(Exception):
    """
    Base domain error. Services raise these and the handler registered in
    app.api.exception_handlers turns them into a response with status_code.
    """

    status_code = 500


class BadRequestError(AppError):
    status_code = 400


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class UnprocessableContentError(AppError):
    status_code = 422
