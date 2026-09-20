from datetime import UTC, datetime, timedelta
from typing import Any
import os

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

password_hash = PasswordHash((Argon2Hasher(),))

ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    """
    Generate a JWT access token for the given subject with an expiration time.
    """
    expire = datetime.now(UTC) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_salt() -> str:
    """
    Generate a new random salt as a hexadecimal string.
    """
    return os.urandom(16).hex()


def hash_with_salt(plain_password: str, salt: str) -> str:
    """
    Helper function to hash a password with a given salt.
    """
    return get_password_hash(f"{plain_password}{salt}")


def hash_password(plain_password: str) -> tuple[str, str]:
    """
    Generate a fresh salt and its corresponding hashed password.
    """
    salt = create_salt()
    return salt, hash_with_salt(plain_password, salt)


def get_password_hash(password: str) -> str:
    """
    Generate a hashed password from the given plain password.
    """
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that the given plain password matches the hashed password.
    """
    return password_hash.verify(plain_password, hashed_password)
