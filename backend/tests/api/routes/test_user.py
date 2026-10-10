import uuid

import pytest
from sqlalchemy import select

from app.models.model import User
from app.schemas.user import UserResponseSchema, UserResponseSchemaPaginated
from seeding.factories import RoleFactory, UserFactory

BASE_URL = "/api/v1/users"


# MARK: GET tests
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
    WHEN a valid user requests a paginated list of all users,
    THEN the response should include the correct number of users for the requested page and size.
    EXPECT the response to be 200 and the pagination metadata to be accurate.
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
    WHEN a valid user attempts to retrieve a user by ID,
    THEN the response should include the user's details if the user exists,
    EXPECT the response status code to be 200 for existing users and 404 for missing users.
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


# MARK: PUT tests
@pytest.mark.parametrize(
    "request_body, expected_status_code",
    [
        pytest.param(
            {
                "username": "valid-all-fields",
                "email": "valid-all-fields@test.example.com",
                "givenName": "Updated",
                "familyName": "User",
                "emailVerified": True,
                "isActive": False,
            },
            200,
            id="valid-all-fields",
        ),
        pytest.param(
            {
                "username": "valid-unset-name",
                "email": "valid-unset-name@test.example.com",
                "givenName": None,
                "familyName": None,
                "emailVerified": True,
                "isActive": False,
            },
            200,
            id="valid-unset-name",
        ),
        pytest.param(
            {
                "username": "valid-no-name",
                "email": "valid-no-name@test.example.com",
                "emailVerified": True,
                "isActive": False,
            },
            200,
            id="valid-no-name",
        ),
        pytest.param(
            {
                "username": None,
                "email": None,
                "emailVerified": True,
                "isActive": False,
            },
            422,
            id="invalid-no-username-email",
        ),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_put_update_user_by_id(
    db_session,
    client,
    auth_headers,
    request_body,
    expected_status_code,
):
    """
    WHEN a valid user attempts to update a user by ID,
    THEN the response should reflect the updated user details if the update is successful,
    EXPECT the response status code to be 200 for successful updates, 404 for missing users, and 422 for validation errors.
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()

    response = client.put(
        f"{BASE_URL}/{user.user_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = UserResponseSchema.model_validate(response.json())
    expected = UserResponseSchema.model_validate(
        {"userId": user.user_id, "givenName": None, "familyName": None} | request_body
    )

    assert validated_body == expected


@pytest.mark.parametrize("conflicting_field", ["username", "email"])
@pytest.mark.usefixtures("act_as_admin")
def test_put_update_user_conflicting_field(
    db_session, client, auth_headers, conflicting_field
):
    """
    WHEN a valid user attempts to update a user with a value already held by another user,
    THEN the response should indicate a conflict,
    EXPECT the response to be 409 with a message naming the conflicting field.
    """

    user = UserFactory.build()
    conflicting_user = UserFactory.build()
    db_session.add_all([user, conflicting_user])
    db_session.flush()

    # reuse a value already held by another user
    request_body = {
        "username": user.username,
        "email": user.email,
        "givenName": user.given_name,
        "familyName": user.family_name,
        "emailVerified": user.email_verified,
        "isActive": user.is_active,
    } | {conflicting_field: getattr(conflicting_user, conflicting_field)}

    response = client.put(
        f"{BASE_URL}/{user.user_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == 409
    assert f"{conflicting_field.capitalize()} already in use" in response.text


# MARK: PATCH tests
@pytest.mark.parametrize(
    "user_exists, request_body, expected_status_code",
    [
        pytest.param(True, {"givenName": "Patched"}, 200, id="single-field"),
        pytest.param(
            True,
            {"username": "patched-user", "isActive": False},
            200,
            id="multiple-fields",
        ),
        pytest.param(True, {}, 200, id="empty-body"),
        pytest.param(False, {"givenName": "Patched"}, 404, id="missing-user"),
        pytest.param(True, {"username": None}, 422, id="null-required-field"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_patch_update_user_by_id(
    db_session,
    client,
    auth_headers,
    user_exists,
    request_body,
    expected_status_code,
):
    """
    WHEN a valid user attempts to partially update a user by ID, leaving omitted
    fields untouched,
    THEN the response should reflect the updated user details if the update is successful,
    EXPECT the response status code to be 200 for successful updates, 404 for missing users, and 422 for validation errors.
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()
    user_id = user.user_id if user_exists else uuid.uuid4()
    original = UserResponseSchema.model_validate(user)

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


@pytest.mark.parametrize("conflicting_field", ["username", "email"])
def test_patch_update_user_conflicting_field(
    db_session, client, act_as_admin, auth_headers, conflicting_field
):
    """
    WHEN a valid user attempts to patch a user with a value already held by another user,
    THEN the response should indicate a conflict,
    EXPECT the response to be 409 with a message naming the conflicting field.
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()

    # reuse a value already held by another user
    request_body = {conflicting_field: getattr(act_as_admin, conflicting_field)}

    response = client.patch(
        f"{BASE_URL}/{user.user_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == 409
    assert f"{conflicting_field.capitalize()} already in use" in response.text


@pytest.mark.parametrize(
    "method, request_body",
    [
        pytest.param(
            "put",
            {
                "username": "self",
                "email": "self@test.example.com",
                "givenName": "Updated",
                "familyName": "User",
                "emailVerified": True,
                "isActive": False,
            },
            id="put",
        ),
        pytest.param("patch", {"isActive": False}, id="patch"),
    ],
)
def test_update_user_updating_self(
    db_session, client, act_as_admin, auth_headers, method, request_body
):
    """
    WHEN a user attempts to update their own account,
    THEN the response should indicate forbidden action,
    EXPECT the response to be 403 and the user to be unchanged
    """

    original = UserResponseSchema.model_validate(act_as_admin)

    response = client.request(
        method,
        f"{BASE_URL}/{act_as_admin.user_id}",
        json=request_body,
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert "Users cannot update their own account" in response.text

    # the user should be unchanged since self-update is forbidden
    db_session.refresh(act_as_admin)
    assert UserResponseSchema.model_validate(act_as_admin) == original


# MARK: DELETE tests
@pytest.mark.usefixtures("act_as_admin")
def test_delete_existing_user_by_id(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to delete an existing user by ID
    THEN the response should indicate successful deletion
    EXPECT the response to be 204
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()

    response = client.delete(f"{BASE_URL}/{user.user_id}", headers=auth_headers)

    assert response.status_code == 204

    # the target user is only gone if it was the one deleted
    db_user = db_session.scalars(
        select(User).where(User.user_id == user.user_id)
    ).one_or_none()

    assert db_user is None


@pytest.mark.usefixtures("act_as_admin")
def test_delete_non_existing_user_by_id(client, auth_headers):
    """
    WHEN a valid user attempts to delete a non-existing user by ID,
    THEN the response should indicate the user was not found,
    EXPECT the response to be 404
    """

    response = client.delete(f"{BASE_URL}/{uuid.uuid7()}", headers=auth_headers)

    assert response.status_code == 404
    assert "User not found" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_delete_existing_user_by_id_twice(db_session, client, auth_headers):
    """
    WHEN the user is deleted and then the endpoint is called again
    THEN the first response should indicate successful deletion and the second that the user was not found
    EXPECT the response to be 204 then 404
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()
    user_id = user.user_id
    response = client.delete(f"{BASE_URL}/{user_id}", headers=auth_headers)

    assert response.status_code == 204

    # the target user is only gone if it was the one deleted
    db_user = db_session.scalars(
        select(User).where(User.user_id == user_id)
    ).one_or_none()

    assert db_user is None

    response = client.delete(f"{BASE_URL}/{user_id}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.usefixtures("act_as_admin")
def test_delete_user_referenced_as_auditor(db_session, client, auth_headers):
    """
    WHEN a user who is recorded as created_by/modified_by on other rows is deleted,
    THEN the deletion should succeed and those audit references should be cleared,
    EXPECT the response to be 204 and the audit columns to be null
    """

    auditor = UserFactory.build()
    db_session.add(auditor)
    db_session.flush()

    # one users row (self-referencing FK) and one AuditMixin row
    audited_user = UserFactory.build(
        created_by=auditor.user_id, modified_by=auditor.user_id
    )
    audited_role = RoleFactory.build(
        created_by=auditor.user_id, modified_by=auditor.user_id
    )
    db_session.add_all([audited_user, audited_role])
    db_session.flush()

    response = client.delete(f"{BASE_URL}/{auditor.user_id}", headers=auth_headers)

    assert response.status_code == 204

    # ON DELETE SET NULL happens in the database, so reload what the session holds
    for row in (audited_user, audited_role):
        db_session.refresh(row)
        assert (row.created_by, row.modified_by) == (None, None)


def test_delete_user_deleting_self(db_session, client, act_as_admin, auth_headers):
    """
    WHEN a user attempts to delete their own account,
    THEN the response should indicate forbidden action,
    EXPECT the response to be 403
    """

    response = client.delete(f"{BASE_URL}/{act_as_admin.user_id}", headers=auth_headers)

    assert response.status_code == 403
    assert "Users cannot delete their own account" in response.text

    # the target user should still exist since self-deletion is forbidden
    db_user = db_session.scalars(
        select(User).where(User.user_id == act_as_admin.user_id)
    ).one_or_none()

    assert db_user is not None
