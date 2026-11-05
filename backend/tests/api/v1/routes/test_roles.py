import pytest
from sqlalchemy import select

from app.core.app_permissions import AppPermissions
from app.models.model import Role, RolePermission, UserRole
from app.schemas.role import RoleSchema, RoleSchemaPaginated
from seeding.factories import RoleFactory, UserFactory

BASE_URL = "/api/v1/roles"


# MARK: GET tests
@pytest.mark.parametrize(
    "num_seed_roles, page, size",
    [
        pytest.param(20, 1, 10, id="default"),
        pytest.param(20, 2, 5, id="second_page"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_get_all_users(db_session, client, auth_headers, num_seed_roles, page, size):
    """
    WHEN a valid user requests a paginated list of all roles,
    THEN the response should include the correct number of roles for the requested page and size.
    EXPECT the response to be 200 and the pagination metadata to be accurate.
    """

    roles = RoleFactory.build_batch(num_seed_roles)
    db_session.add_all(roles)
    db_session.flush()

    total_in_db = len(db_session.scalars(select(Role)).all())
    response = client.get(
        f"{BASE_URL}?page={page}&size={size}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()

    validated_body = RoleSchemaPaginated.model_validate(body)

    assert len(validated_body.items) == size
    assert validated_body.total == total_in_db
    assert validated_body.page == page
    assert validated_body.size == size


@pytest.mark.parametrize(
    "role_id, seed_role, expected_status_code",
    [
        pytest.param("admin", False, 200, id="existing-core-role"),
        pytest.param("a_new_role", True, 200, id="existing-new-role"),
        pytest.param("a_new_role", False, 404, id="missing-role"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_get_role_by_id(
    db_session, client, auth_headers, role_id, seed_role, expected_status_code
):
    """
    WHEN a valid user attempts to retrieve a role by ID,
    THEN the response should include the role's details if the role exists,
    EXPECT the response status code to be 200 for existing roles and 404 for missing roles.
    """
    if seed_role:
        role = RoleFactory.build(role_id=role_id)
        db_session.add(role)
        db_session.flush()

    response = client.get(f"{BASE_URL}/{role_id}", headers=auth_headers)

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = RoleSchema.model_validate(response.json())

    assert validated_body.role_id == role_id


# MARK: POST tests
@pytest.mark.parametrize(
    "request_body, expected_status_code",
    [
        pytest.param(
            {
                "roleId": "valid-all-fields",
                "name": "Valid all fields",
                "description": "A new role",
            },
            201,
            id="valid-all-fields",
        ),
        pytest.param(
            {"roleId": "missing-name", "description": "A new role"},
            422,
            id="invalid-missing-name",
        ),
        pytest.param(
            {"name": "Missing role id", "description": "A new role"},
            422,
            id="invalid-missing-role-id",
        ),
        pytest.param(
            {"roleId": "null-name", "name": None, "description": "A new role"},
            422,
            id="invalid-null-name",
        ),
    ],
)
def test_post_create_role(
    db_session, client, act_as_admin, auth_headers, request_body, expected_status_code
):
    """
    WHEN a valid user attempts to create a role,
    THEN the response should include the new role's details if creation is successful,
    EXPECT the response status code to be 200 for successful creation and 422 for validation errors.
    """

    response = client.post(BASE_URL, json=request_body, headers=auth_headers)

    assert response.status_code == expected_status_code
    if expected_status_code != 201:
        return

    validated_body = RoleSchema.model_validate(response.json())

    assert validated_body.role_id == request_body["roleId"]
    assert validated_body.name == request_body["name"]
    assert validated_body.description == request_body["description"]
    assert validated_body.created_by == act_as_admin.user_id
    assert validated_body.modified_by == act_as_admin.user_id

    db_role = db_session.get(Role, request_body["roleId"])

    assert db_role is not None


@pytest.mark.parametrize(
    "conflicting_field, request_field, expected_message",
    [
        pytest.param("role_id", "roleId", "Role ID already in use", id="role-id"),
        pytest.param("name", "name", "Name already in use", id="name"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_post_create_role_conflicting_field(
    db_session, client, auth_headers, conflicting_field, request_field, expected_message
):
    """
    WHEN a valid user attempts to create a role with a value already held by another role,
    THEN the response should indicate a conflict,
    EXPECT the response to be 409 with a message naming the conflicting field.
    """

    role = RoleFactory.build()
    db_session.add(role)
    db_session.flush()

    # reuse a value already held by another role
    request_body = {
        "roleId": "a_new_role",
        "name": "A new role",
        "description": "A new role",
    } | {request_field: getattr(role, conflicting_field)}

    response = client.post(BASE_URL, json=request_body, headers=auth_headers)

    assert response.status_code == 409
    assert expected_message in response.text


# MARK: PUT tests
@pytest.mark.parametrize(
    "role_exists, request_body, expected_status_code",
    [
        pytest.param(
            True,
            {"name": "Updated name", "description": "Updated description"},
            200,
            id="valid-all-fields",
        ),
        pytest.param(
            False,
            {"name": "Updated name", "description": "Updated description"},
            404,
            id="missing-role",
        ),
        pytest.param(
            True, {"description": "Updated description"}, 422, id="invalid-no-name"
        ),
        pytest.param(
            True,
            {"name": None, "description": "Updated description"},
            422,
            id="invalid-null-name",
        ),
    ],
)
def test_put_update_role_by_id(
    db_session,
    client,
    act_as_admin,
    auth_headers,
    role_exists,
    request_body,
    expected_status_code,
):
    """
    WHEN a valid user attempts to update a role by ID,
    THEN the response should reflect the updated role details if the update is successful,
    EXPECT the response status code to be 200 for successful updates, 404 for missing roles, and 422 for validation errors.
    """

    role = RoleFactory.build()
    db_session.add(role)
    db_session.flush()
    role_id = role.role_id if role_exists else "a_missing_role"

    response = client.put(
        f"{BASE_URL}/{role_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = RoleSchema.model_validate(response.json())

    assert validated_body.role_id == role_id
    assert validated_body.name == request_body["name"]
    assert validated_body.description == request_body["description"]
    assert validated_body.modified_by == act_as_admin.user_id


@pytest.mark.usefixtures("act_as_admin")
def test_put_update_role_conflicting_name(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to update a role with a name already held by another role,
    THEN the response should indicate a conflict,
    EXPECT the response to be 409 with a message naming the conflicting field.
    """

    role = RoleFactory.build()
    conflicting_role = RoleFactory.build()
    db_session.add_all([role, conflicting_role])
    db_session.flush()

    # reuse a value already held by another role
    request_body = {"name": conflicting_role.name, "description": role.description}

    response = client.put(
        f"{BASE_URL}/{role.role_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == 409
    assert "Name already in use" in response.text


# MARK: PATCH tests
@pytest.mark.parametrize(
    "role_exists, request_body, expected_status_code",
    [
        pytest.param(True, {"name": "Patched"}, 200, id="single-field"),
        pytest.param(
            True,
            {"name": "Patched", "description": "Patched description"},
            200,
            id="multiple-fields",
        ),
        pytest.param(True, {}, 200, id="empty-body"),
        pytest.param(False, {"name": "Patched"}, 404, id="missing-role"),
        pytest.param(True, {"name": None}, 422, id="null-name"),
        pytest.param(True, {"description": None}, 422, id="null-description"),
    ],
)
def test_patch_update_role_by_id(
    db_session,
    client,
    act_as_admin,
    auth_headers,
    role_exists,
    request_body,
    expected_status_code,
):
    """
    WHEN a valid user attempts to partially update a role by ID, leaving omitted
    fields untouched,
    THEN the response should reflect the updated role details if the update is successful,
    EXPECT the response status code to be 200 for successful updates, 404 for missing roles, and 422 for validation errors.
    """

    role = RoleFactory.build()
    db_session.add(role)
    db_session.flush()
    role_id = role.role_id if role_exists else "a_missing_role"
    original = {"name": role.name, "description": role.description}

    response = client.patch(
        f"{BASE_URL}/{role_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = RoleSchema.model_validate(response.json())
    expected = original | request_body

    assert validated_body.role_id == role_id
    assert validated_body.name == expected["name"]
    assert validated_body.description == expected["description"]
    assert validated_body.modified_by == act_as_admin.user_id


@pytest.mark.usefixtures("act_as_admin")
def test_patch_update_role_conflicting_name(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to patch a role with a name already held by another role,
    THEN the response should indicate a conflict,
    EXPECT the response to be 409 with a message naming the conflicting field.
    """

    role = RoleFactory.build()
    conflicting_role = RoleFactory.build()
    db_session.add_all([role, conflicting_role])
    db_session.flush()

    # reuse a value already held by another role
    request_body = {"name": conflicting_role.name}

    response = client.patch(
        f"{BASE_URL}/{role.role_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == 409
    assert "Name already in use" in response.text


# MARK: DELETE tests
@pytest.mark.usefixtures("act_as_admin")
def test_delete_role_by_id(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to delete an existing role by ID
    THEN the response should indicate successful deletion
    EXPECT the response to be 204
    """

    role = RoleFactory.build()
    db_session.add(role)
    db_session.flush()
    role_id = role.role_id

    response = client.delete(f"{BASE_URL}/{role_id}", headers=auth_headers)

    assert response.status_code == 204

    # the target role is only gone if it was the one deleted
    db_role = db_session.scalars(
        select(Role).where(Role.role_id == role_id)
    ).one_or_none()

    assert db_role is None


@pytest.mark.usefixtures("act_as_admin")
def test_delete_non_existing_role_by_id(client, auth_headers):
    """
    WHEN a valid user attempts to delete a non-existing role by ID,
    THEN the response should indicate the role was not found,
    EXPECT the response to be 404
    """

    response = client.delete(f"{BASE_URL}/a_missing_role", headers=auth_headers)

    assert response.status_code == 404
    assert "Role not found" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_delete_existing_role_by_id_twice(db_session, client, auth_headers):
    """
    WHEN the role is deleted and then the endpoint is called again
    THEN the first response should indicate successful deletion and the second that the role was not found
    EXPECT the response to be 204 then 404
    """

    role = RoleFactory.build()
    db_session.add(role)
    db_session.flush()
    role_id = role.role_id

    response = client.delete(f"{BASE_URL}/{role_id}", headers=auth_headers)

    assert response.status_code == 204

    response = client.delete(f"{BASE_URL}/{role_id}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.usefixtures("act_as_admin")
def test_delete_role_assigned_to_user(
    db_session, client, auth_headers, grant_permissions
):
    """
    WHEN a role that is assigned to a user and holds permissions is deleted,
    THEN the deletion should succeed and the role's assignments should be removed,
    EXPECT the response to be 204 and no user_roles or role_permissions rows to remain
    """

    user = UserFactory.build()
    db_session.add(user)
    db_session.flush()
    role_id = grant_permissions(user, [AppPermissions.READ__USERS]).role_id

    response = client.delete(f"{BASE_URL}/{role_id}", headers=auth_headers)

    assert response.status_code == 204

    # ON DELETE CASCADE happens in the database, so query rather than trust the session
    for model in (UserRole, RolePermission):
        rows = db_session.scalars(select(model).where(model.role_id == role_id)).all()
        assert rows == []
