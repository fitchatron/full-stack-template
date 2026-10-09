import uuid

import pytest
from sqlalchemy import select

from app.models.model import User
from app.schemas.user import UserResponseSchema, UserResponseSchemaPaginated
from seeding.factories import UserFactory

BASE_URL = "/api/v1/users"


@pytest.mark.parametrize(
    "num_seed_users, page, size",
    [
        pytest.param(20, 1, 10, id="default"),
        pytest.param(20, 2, 5, id="second_page"),
    ],
)
def test_get_all_users(
    db_session, client, act_as_admin, auth_headers, num_seed_users, page, size
):
    """
    Test that a valid user can retrieve all users.
    """

    users = UserFactory.build_batch(num_seed_users)
    db_session.add_all(users)
    db_session.flush()

    response = client.get(
        f"{BASE_URL}?page={page}&size={size}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()

    validated_body = UserResponseSchemaPaginated.model_validate(body)

    assert len(validated_body.items) == size
    assert validated_body.total == num_seed_users + len([act_as_admin])
    assert validated_body.page == page
    assert validated_body.size == size


@pytest.mark.parametrize(
    "user_exists, expected_status_code",
    [
        pytest.param(True, 200, id="existing-user"),
        pytest.param(False, 404, id="missing-user"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_get_user_by_id(
    db_session, client, auth_headers, user_exists, expected_status_code
):
    """
    Test that a valid user can retrieve a user by ID.
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()
    user_id = user.user_id if user_exists else uuid.uuid4()

    response = client.get(f"{BASE_URL}/{user_id}", headers=auth_headers)

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = UserResponseSchema.model_validate(response.json())

    assert validated_body.user_id == user.user_id
    assert validated_body.username == user.username
    assert validated_body.email == user.email


PUT_REQUEST = {
    "username": "updated-user",
    "email": "updated-user@test.example.com",
    "givenName": "Updated",
    "familyName": "User",
    "emailVerified": True,
    "isActive": False,
}


@pytest.mark.parametrize(
    "user_exists, request_body, conflicting_field, expected_status_code",
    [
        pytest.param(True, PUT_REQUEST, None, 200, id="valid"),
        pytest.param(
            True,
            {
                k: v
                for k, v in PUT_REQUEST.items()
                if k not in ("givenName", "familyName")
            },
            None,
            200,
            id="valid-no-name",
        ),
        pytest.param(False, PUT_REQUEST, None, 404, id="missing-user"),
        pytest.param(True, PUT_REQUEST, "username", 409, id="username-taken"),
        pytest.param(True, PUT_REQUEST, "email", 409, id="email-taken"),
        pytest.param(
            True,
            {k: v for k, v in PUT_REQUEST.items() if k != "email"},
            None,
            422,
            id="missing-required-field",
        ),
    ],
)
def test_put_update_user_by_id(
    db_session,
    client,
    act_as_admin,
    auth_headers,
    user_exists,
    request_body,
    conflicting_field,
    expected_status_code,
):
    """
    Test that a valid user can replace a user by ID.
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()
    user_id = user.user_id if user_exists else uuid.uuid4()

    if conflicting_field:
        # reuse a value already held by another user
        request_body = request_body | {
            conflicting_field: getattr(act_as_admin, conflicting_field)
        }

    response = client.put(
        f"{BASE_URL}/{user_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = UserResponseSchema.model_validate(response.json())
    expected = UserResponseSchema.model_validate(
        {"userId": user.user_id, "givenName": None, "familyName": None} | request_body
    )

    assert validated_body == expected


@pytest.mark.parametrize(
    "user_exists, request_body, conflicting_field, expected_status_code",
    [
        pytest.param(True, {"givenName": "Patched"}, None, 200, id="single-field"),
        pytest.param(
            True,
            {"username": "patched-user", "isActive": False},
            None,
            200,
            id="multiple-fields",
        ),
        pytest.param(True, {}, None, 200, id="empty-body"),
        pytest.param(False, {"givenName": "Patched"}, None, 404, id="missing-user"),
        pytest.param(True, {}, "username", 409, id="username-taken"),
        pytest.param(True, {}, "email", 409, id="email-taken"),
        pytest.param(True, {"username": None}, None, 422, id="null-required-field"),
    ],
)
def test_patch_update_user_by_id(
    db_session,
    client,
    act_as_admin,
    auth_headers,
    user_exists,
    request_body,
    conflicting_field,
    expected_status_code,
):
    """
    Test that a valid user can partially update a user by ID, leaving omitted
    fields untouched.
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()
    user_id = user.user_id if user_exists else uuid.uuid4()
    original = UserResponseSchema.model_validate(user)

    if conflicting_field:
        # reuse a value already held by another user
        request_body = request_body | {
            conflicting_field: getattr(act_as_admin, conflicting_field)
        }

    response = client.patch(
        f"{BASE_URL}/{user_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = UserResponseSchema.model_validate(response.json())
    expected = UserResponseSchema.model_validate(
        original.model_dump(by_alias=True) | request_body
    )

    assert validated_body == expected


@pytest.mark.parametrize(
    "user_exists, expected_status_code",
    [
        pytest.param(True, 204, id="existing-user"),
        pytest.param(False, 404, id="missing-user"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_delete_user_by_id(
    db_session, client, auth_headers, user_exists, expected_status_code
):
    """
    Test that a valid user can delete a user by ID.
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()
    user_id = user.user_id if user_exists else uuid.uuid4()

    response = client.delete(f"{BASE_URL}/{user_id}", headers=auth_headers)

    assert response.status_code == expected_status_code

    # the target user is only gone if it was the one deleted
    db_user = db_session.scalars(
        select(User).where(User.user_id == user.user_id)
    ).one_or_none()
    assert (db_user is None) == user_exists
