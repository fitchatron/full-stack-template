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


def verify_token(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)

        return token_data
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


VerifyTokenDep = Annotated[User, Depends(verify_token)]


class AuthorizeUser:
    """
    Dependency class to authorize user by verifying token and checking user permission at application level
    """

    def __init__(
        self,
        required_permissions: list[str] | None = None,
    ):
        self.required_permissions = required_permissions

    def _is_authorized(self, session: Session, user_id: int) -> bool:

        # if required permissions is None, then endpoint can be executed without any permission
        # as long as user is authenticated
        if self.required_permissions is None:
            return True

        # get all permissions attached to the user
        permissions = UserService(session).read_all_permissions_for_user_id(user_id)
        authorized = any(
            permission.permission_id in self.required_permissions
            for permission in permissions
        )

        return authorized

    def __call__(self, token: VerifyTokenDep, session: SessionDep) -> User:

        # register user
        user = self._register_user(session, token.sub)

        # check permisison
        if not self._is_authorized(session, user.user_id):
            raise HTTPException(status_code=403)

        # return user
        return user
