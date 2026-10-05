import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core import security
from app.core.config import settings


def decode(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])


# MARK: create_access_token
def test_create_access_token_round_trips_uuid_subject():
    user_id = uuid.uuid4()

    payload = decode(security.create_access_token(user_id, timedelta(minutes=5)))

    assert uuid.UUID(payload["sub"]) == user_id


def test_create_access_token_sets_expiry_from_delta():
    before = datetime.now(UTC)

    payload = decode(security.create_access_token("subject", timedelta(minutes=5)))

    expires_at = datetime.fromtimestamp(payload["exp"], UTC)
    # exp is stored in whole seconds, so allow for truncation
    assert (
        before + timedelta(minutes=5) - timedelta(seconds=1)
        <= expires_at
        <= datetime.now(UTC) + timedelta(minutes=5)
    )


def test_create_access_token_expired_token_is_rejected():
    token = security.create_access_token("subject", timedelta(seconds=-1))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode(token)


def test_create_access_token_is_rejected_with_wrong_key():
    token = security.create_access_token("subject", timedelta(minutes=5))

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            token,
            "not-the-secret-key-but-long-enough-for-hs256",
            algorithms=[security.ALGORITHM],
        )


# MARK: password hashing
def test_hash_password_returns_salt_then_hash():
    salt, hashed = security.hash_password("Password123!")

    assert verify_salted("Password123!", salt, hashed)


def test_hash_password_generates_a_new_salt_each_time():
    first_salt, _ = security.hash_password("Password123!")
    second_salt, _ = security.hash_password("Password123!")

    assert first_salt != second_salt


@pytest.mark.parametrize(
    "password, use_correct_salt, expected",
    [
        pytest.param("Password123!", True, True, id="correct_password_and_salt"),
        pytest.param("WrongPassword!", True, False, id="wrong_password"),
        pytest.param("Password123!", False, False, id="wrong_salt"),
    ],
)
def test_hash_with_salt_verifies_with_password_then_salt(
    password, use_correct_salt, expected
):
    """
    Login (services/auth.py) verifies f"{password}{salt}" against the stored hash,
    so hashing must use the same order.
    """
    salt = security.create_salt()
    hashed = security.hash_with_salt("Password123!", salt)
    verify_with_salt = salt if use_correct_salt else security.create_salt()

    assert verify_salted(password, verify_with_salt, hashed) is expected


def verify_salted(password: str, salt: str, hashed: str) -> bool:
    return security.verify_password(f"{password}{salt}", hashed)
