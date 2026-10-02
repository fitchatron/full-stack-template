import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import create_access_token
from app.models.model import User
from app.schemas.auth import Token
from seeding.factories import UserFactory


@pytest.mark.parametrize(
    "register_user_request, expected_status_code",
    [
        pytest.param(
            {
                "email": "new-user-valid@test.example.com",
                "username": "new-user-valid",
                "given_name": "New",
                "family_name": "User",
                "password": "ValidPassword123!",
                "password_confirm": "ValidPassword123!",
            },
            200,
            id="valid-registration",
        ),
        pytest.param(
            {
                "email": "new-user-valid@test.example.com",
                "username": "new-user-valid",
                "password": "ValidPassword123!",
                "password_confirm": "ValidPassword123!",
            },
            200,
            id="valid-registration-no-name",
        ),
        pytest.param(
            {
                "email": "new-user-invalid@test.example.com",
                "username": "new-user-invalid",
                "given_name": "New",
                "family_name": "User",
                "password": "ValidPassword123!",
                "password_confirm": "InvalidPassword123!",
            },
            422,
            id="invalid-registration-password-mismatch",
        ),
    ],
)
def test_register(client, register_user_request, expected_status_code):
    """
    Test the registration functionality for a new user.
    """

    response = client.post(
        "/api/v1/auth/register",
        json=register_user_request,
    )

    assert response.status_code == expected_status_code


def test_register_existing_user(client, db_session):
    """
    Test that registering an existing user returns a 400 status code with the appropriate error message.
    """
    existing_user = UserFactory.build(email="existing-user@test.example.com")
    db_session.add(existing_user)
    db_session.flush()

    db_user = db_session.scalars(
        select(User).where(User.email == existing_user.email)
    ).one_or_none()

    assert db_user is not None
    assert existing_user.email == db_user.email

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "existing-user@test.example.com",
            "username": "existing-user",
            "given_name": "I",
            "family_name": "Exist",
            "password": "ValidPassword123!",
            "password_confirm": "ValidPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.parametrize(
    "use_fixture_email, password, expected_status_code, expected_response_json",
    [
        pytest.param(
            True,
            settings.TEST_USER_PASSWORD,
            200,
            {"access_token": "", "token_type": "bearer"},
        ),
        pytest.param(
            True,
            "wrong-password",
            400,
            {"detail": "Incorrect email or password"},
            id="wrong-password-using-fixture-email",
        ),
        pytest.param(
            False,
            "wrong-password",
            400,
            {"detail": "Incorrect email or password"},
            id="wrong-password-not-using-fixture-email",
        ),
    ],
)
def test_login_user(
    client,
    act_as_user,
    use_fixture_email,
    password,
    expected_status_code,
    expected_response_json,
):
    """
    Test the login functionality for a user.
    """
    email = act_as_user.email if use_fixture_email else "non-existent@email.test.com"
    response = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )

    assert response.status_code == expected_status_code
    if response.status_code == 200:
        assert (
            expected_response_json
            | {"access_token": response.json().get("access_token")}
            == response.json()
        )
    else:
        assert response.json() == expected_response_json


def test_test_token_valid_user(client, act_as_admin):
    """
    Test that a valid user with a valid token can validate the token.
    """
    token = Token(
        access_token=create_access_token(
            act_as_admin.user_id, expires_delta=timedelta(minutes=5)
        )
    )

    response = client.post(
        "/api/v1/auth/test-token",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["userId"] == str(act_as_admin.user_id)


def test_test_token_valid_user_expired_token(client, act_as_admin):
    """
    Test that a valid user with an expired token cannot validate the token.
    """
    token = Token(
        access_token=create_access_token(
            act_as_admin.user_id, expires_delta=timedelta(minutes=-5)
        )
    )

    response = client.post(
        "/api/v1/auth/test-token",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Could not validate credentials"


def test_test_token_invalid_user(client):
    """
    Test that an invalid user with a non-existent UUID cannot validate the token.
    """
    token = Token(
        access_token=create_access_token(
            uuid.uuid4(), expires_delta=timedelta(minutes=-5)
        )
    )

    response = client.post(
        "/api/v1/auth/test-token",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Could not validate credentials"
