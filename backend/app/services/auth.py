from datetime import timedelta
import os
from fastapi import HTTPException
from pydantic import SecretStr
from sqlalchemy.orm import Session
from app.models.model import User
from app.repositories.user import UserRepository
from app.core.config import settings
from app.schemas.auth import Token

from app.core.security import create_access_token, verify_password, get_password_hash

# from app.schemas.user import RegisterUserPOSTRequest
from app.schemas.filter_generator import (
    ComparisonOperator,
    FilterCondition,
    FilterPayload,
)
from app.schemas.user import RegisterUserPOSTRequest, RegisterUserSchema


class AuthService:
    # Dummy hash to use for timing attack prevention when user is not found
    # This is an Argon2 hash of a random password, used to ensure constant-time comparison
    DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"

    def __init__(self, session: Session) -> None:
        """
        AuthService constructor.
        """

        self.user_repo = UserRepository(session, User)
        self.session = session

    def authenticate(self, email: str, password: str):
        user = self.user_repo.read_user_by_email(email=email)

        if not user:
            # Prevent timing attacks by running password verification even when user doesn't exist
            # This ensures the response time is similar whether or not the email exists
            verify_password(password, self.DUMMY_HASH)
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        verified = verify_password(f"{password}{user.salt}", user.hashed_password)

        if not verified:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        if verified and not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return Token(
            access_token=create_access_token(
                user.user_id, expires_delta=access_token_expires
            )
        )

    def register(self, request: RegisterUserPOSTRequest):

        user = self.user_repo.read_user_by_email(email=request.email)
        if user:
            raise HTTPException(status_code=400, detail="Email already registered")
        salt = os.urandom(16).hex()
        password_hash = get_password_hash(
            f"{request.password.get_secret_value()}{salt}"
        )
        user_data = RegisterUserSchema(
            email=request.email,
            username=request.username,
            given_name=request.given_name,
            family_name=request.family_name,
            hashed_password=SecretStr(password_hash),
            salt=salt,
        )

        new_user = self.user_repo.create_user(user_data=user_data)

        if not new_user:
            raise HTTPException(status_code=500, detail="Failed to create user")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return Token(
            access_token=create_access_token(
                new_user.user_id, expires_delta=access_token_expires
            )
        )
