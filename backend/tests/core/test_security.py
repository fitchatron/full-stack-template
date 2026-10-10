import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core import security
from app.core.config import settings


def decode(token: str) -> dict:
    """
    Decodes a JWT token using the application's secret key and the specified algorithm.
    Returns the decoded payload as a dictionary.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])


# MARK: create_access_token
def test_create_access_token_round_trips_uuid_subject():
    """
    WHEN an access token is created with a UUID subject,
    THEN decoding the token should yield the same UUID in the "sub" claim.
    EXPECT the decoded UUID to match the original UUID used to create the token.
    """
    user_id = uuid.uuid7()

    payload = decode(security.create_access_token(user_id, timedelta(minutes=5)))

    assert uuid.UUID(payload["sub"]) == user_id


def test_create_access_token_sets_expiry_from_delta():
    """
    WHEN an access token is created with a specific expiry delta,
    THEN the "exp" claim in the token should reflect the correct expiry time.
    EXPECT the expiry time to be within the expected range considering possible truncation to whole seconds.
    """
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
    """
    WHEN an access token is created with an expiry time in the past,
    THEN decoding the token should raise an ExpiredSignatureError.
    EXPECT the token to be rejected due to expiration.
    """
    token = security.create_access_token("subject", timedelta(seconds=-1))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode(token)


def test_create_access_token_is_rejected_with_wrong_key():
    """
    WHEN an access token is decoded with an incorrect secret key,
    THEN decoding the token should raise an InvalidSignatureError.
    EXPECT the token to be rejected due to the wrong key.
    """
    token = security.create_access_token("subject", timedelta(minutes=5))

    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(
            token,
            "not-the-secret-key-but-long-enough-for-hs256",
            algorithms=[security.ALGORITHM],
        )


# MARK: password hashing
def test_hash_password_returns_salt_then_hash():
    """
    WHEN a password is hashed,
    THEN the function should return a salt and the corresponding hashed password.
    EXPECT the hashed password to be verifiable using the returned salt.
    """
    salt, hashed = security.hash_password("Password123!")

    assert verify_salted("Password123!", salt, hashed)


def test_hash_password_generates_a_new_salt_each_time():
    """
    WHEN the same password is hashed multiple times,
    THEN each invocation should generate a unique salt.
    EXPECT the salts to be different for each hashing operation.
    """
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
    WHEN a password is hashed with a salt,
    THEN verifying the password with the correct or incorrect salt should yield the expected result.
    EXPECT the verification to succeed only when the correct salt is used.
    """
    salt = security.create_salt()
    hashed = security.hash_with_salt("Password123!", salt)
    verify_with_salt = salt if use_correct_salt else security.create_salt()

    assert verify_salted(password, verify_with_salt, hashed) is expected


def verify_salted(password: str, salt: str, hashed: str) -> bool:
    return security.verify_password(f"{password}{salt}", hashed)
