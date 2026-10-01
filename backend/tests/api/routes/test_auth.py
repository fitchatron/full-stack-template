import pytest


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
            400,
            id="invalid-registration",
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
