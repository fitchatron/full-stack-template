from sqlalchemy.orm import Session
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from collections.abc import Generator
from app.core.db import SessionLocal
import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.models import User
from app.services.user import UserService
from app.schemas.auth import TokenPayload
from app.core import security

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


# FastAPI dependency: yields a session per request, closing it afterwards
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


class AuthorizeUser:
    """
    Dependency class to authorize user by verifying token and checking user permission at application level
    """

    def __init__(
        self,
        required_permissions: list[str] | None = None,
    ):
        self.required_permissions = required_permissions

    def __call__(self, token: TokenDep, session: SessionDep) -> User:

        user = self._get_current_user(session, token)
        # check permisison
        if not self._is_authorized(session, user.user_id):
            raise HTTPException(status_code=403)

        # return user
        return user

    def _is_authorized(self, session: Session, user_id: int) -> bool:
        """
        Checks if the user has the required permissions.

        Returns True if the user is authorized, False otherwise.
        """
        # if required permissions is None, then endpoint can be executed without any permission
        # as long as user is authenticated
        if self.required_permissions is None:
            return True

        # get all permissions attached to the user
        permissions = UserService(session).read_active_permissions_for_user_id(user_id)
        authorized = any(
            permission.permission_id in self.required_permissions
            for permission in permissions
        )

        return authorized

    def _get_current_user(self, session: SessionDep, token: TokenDep) -> User:
        """
        Retrieves the current user based on the provided token.

        Raises HTTPException if the token is invalid, the user is not found, or the user is inactive.

        Returns the User object.
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
        except (InvalidTokenError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
        user = UserService(session).read_by_id(token_data.sub)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user
