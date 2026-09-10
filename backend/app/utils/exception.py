from fastapi import HTTPException, status
from typing import Any


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


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


class UnprocessableContentError(Exception):
    pass
