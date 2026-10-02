import pytest
from sqlalchemy import select

from app.models.model import User
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
    1. register new user valid details
    2. register new user invalid details
    3. register existing user
    """

    response = client.post(
        "/api/v1/auth/register",
        json=register_user_request,
    )

    assert response.status_code == expected_status_code


def test_register_existing_user(client, db_session):
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
