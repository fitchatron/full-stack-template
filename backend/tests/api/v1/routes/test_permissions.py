import uuid

import pytest
from sqlalchemy import select

from app.core.app_permissions import AppPermissions
from app.models.enums import AuthorizationAction
from app.models.model import Permission, RolePermission
from app.schemas.permission import PermissionSchema, PermissionSchemaPaginated
from seeding.factories import PermissionFactory, RolePermissionFactory

BASE_URL = "/api/v1/permissions"
MISSING_PERMISSION_ID = uuid.UUID(int=0)


# MARK: GET tests
@pytest.mark.parametrize(
    "num_seed_permissions, page, size",
    [
        pytest.param(20, 1, 10, id="default"),
        pytest.param(20, 2, 5, id="second_page"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_get_all_permissions(
    db_session, client, auth_headers, num_seed_permissions, page, size
):
    """
    WHEN a valid user requests a paginated list of all permissions,
    THEN the response should include the correct number of permissions for the requested page and size.
    EXPECT the response to be 200 and the pagination metadata to be accurate.
    """

    permissions = PermissionFactory.build_batch(num_seed_permissions)
    db_session.add_all(permissions)
    db_session.flush()

    total_in_db = len(db_session.scalars(select(Permission)).all())
    response = client.get(
        f"{BASE_URL}?page={page}&size={size}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()

    validated_body = PermissionSchemaPaginated.model_validate(body)

    assert len(validated_body.items) == size
    assert validated_body.total == total_in_db
    assert validated_body.page == page
    assert validated_body.size == size


@pytest.mark.usefixtures("act_as_admin")
def test_get_permission_by_id_core_permission(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to retrieve a seeded permission by ID,
    THEN the response should include the permission's details,
    EXPECT the response to be 200.
    """

    permission = db_session.scalars(
        select(Permission).where(AppPermissions.READ__USERS.to_filter_clause())
    ).one()

    response = client.get(
        f"{BASE_URL}/{permission.permission_id}", headers=auth_headers
    )

    assert response.status_code == 200

    validated_body = PermissionSchema.model_validate(response.json())

    assert validated_body.permission_id == permission.permission_id
    assert validated_body.action == AuthorizationAction.read
    assert validated_body.resource == "users"


@pytest.mark.parametrize(
    "permission_exists, expected_status_code",
    [
        pytest.param(True, 200, id="existing-new-permission"),
        pytest.param(False, 404, id="missing-permission"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_get_permission_by_id(
    db_session, client, auth_headers, permission_exists, expected_status_code
):
    """
    WHEN a valid user attempts to retrieve a permission by ID,
    THEN the response should include the permission's details if the permission exists,
    EXPECT the response status code to be 200 for existing permissions and 404 for missing permissions.
    """

    permission = PermissionFactory.build()
    db_session.add(permission)
    db_session.flush()
    permission_id = (
        permission.permission_id if permission_exists else MISSING_PERMISSION_ID
    )

    response = client.get(f"{BASE_URL}/{permission_id}", headers=auth_headers)

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = PermissionSchema.model_validate(response.json())

    assert validated_body.permission_id == permission_id


@pytest.mark.usefixtures("act_as_admin")
def test_get_permission_by_invalid_id(client, auth_headers):
    """
    WHEN a valid user attempts to retrieve a permission with an ID that is not a UUID,
    THEN the request should be rejected,
    EXPECT the response to be 422.
    """

    response = client.get(f"{BASE_URL}/not-a-uuid", headers=auth_headers)

    assert response.status_code == 422


# MARK: POST tests
@pytest.mark.parametrize(
    "request_body, expected_status_code",
    [
        pytest.param(
            {
                "action": "read",
                "resource": "valid-all-fields",
                "description": "A new permission",
            },
            201,
            id="valid-all-fields",
        ),
        pytest.param(
            {
                "action": "*",
                "resource": "valid-wildcard-action",
                "description": "A new permission",
            },
            201,
            id="valid-wildcard-action",
        ),
        pytest.param(
            {"resource": "missing-action", "description": "A new permission"},
            422,
            id="invalid-missing-action",
        ),
        pytest.param(
            {"action": "read", "description": "A new permission"},
            422,
            id="invalid-missing-resource",
        ),
        pytest.param(
            {"action": "read", "resource": "missing-description"},
            422,
            id="invalid-missing-description",
        ),
        pytest.param(
            {
                "action": "publish",
                "resource": "unknown-action",
                "description": "A new permission",
            },
            422,
            id="invalid-unknown-action",
        ),
        pytest.param(
            {"action": "read", "resource": None, "description": "A new permission"},
            422,
            id="invalid-null-resource",
        ),
    ],
)
def test_post_create_permission(
    db_session, client, act_as_admin, auth_headers, request_body, expected_status_code
):
    """
    WHEN a valid user attempts to create a permission,
    THEN the response should include the new permission's details if creation is successful,
    EXPECT the response status code to be 201 for successful creation and 422 for validation errors.
    """

    response = client.post(BASE_URL, json=request_body, headers=auth_headers)

    assert response.status_code == expected_status_code
    if expected_status_code != 201:
        return

    validated_body = PermissionSchema.model_validate(response.json())

    assert validated_body.action == request_body["action"]
    assert validated_body.resource == request_body["resource"]
    assert validated_body.description == request_body["description"]
    assert validated_body.created_by == act_as_admin.user_id
    assert validated_body.modified_by == act_as_admin.user_id

    db_permission = db_session.get(Permission, validated_body.permission_id)

    assert db_permission is not None


@pytest.mark.usefixtures("act_as_admin")
def test_post_create_permission_conflicting_action_and_resource(
    db_session, client, auth_headers
):
    """
    WHEN a valid user attempts to create a permission with an action and resource
    pair already held by another permission,
    THEN the response should indicate a conflict,
    EXPECT the response to be 409 with a message naming the conflicting fields.
    """

    permission = PermissionFactory.build()
    db_session.add(permission)
    db_session.flush()

    request_body = {
        "action": permission.action,
        "resource": permission.resource,
        "description": "A new permission",
    }

    response = client.post(BASE_URL, json=request_body, headers=auth_headers)

    assert response.status_code == 409
    assert "Permission already exists" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_post_create_permission_shared_resource(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to create a permission for a resource already held by
    another permission but with a different action,
    THEN the permission should be created as only the pair must be unique,
    EXPECT the response to be 201.
    """

    permission = PermissionFactory.build(action=AuthorizationAction.read)
    db_session.add(permission)
    db_session.flush()

    request_body = {
        "action": "update",
        "resource": permission.resource,
        "description": "A new permission",
    }

    response = client.post(BASE_URL, json=request_body, headers=auth_headers)

    assert response.status_code == 201


# MARK: PUT tests
@pytest.mark.parametrize(
    "permission_exists, request_body, expected_status_code",
    [
        pytest.param(
            True,
            {
                "action": "update",
                "resource": "updated-resource",
                "description": "Updated description",
            },
            200,
            id="valid-all-fields",
        ),
        pytest.param(
            False,
            {
                "action": "update",
                "resource": "updated-resource",
                "description": "Updated description",
            },
            404,
            id="missing-permission",
        ),
        pytest.param(
            True,
            {"action": "update", "description": "Updated description"},
            422,
            id="invalid-no-resource",
        ),
        pytest.param(
            True,
            {
                "action": None,
                "resource": "updated-resource",
                "description": "Updated description",
            },
            422,
            id="invalid-null-action",
        ),
    ],
)
def test_put_update_permission_by_id(
    db_session,
    client,
    act_as_admin,
    auth_headers,
    permission_exists,
    request_body,
    expected_status_code,
):
    """
    WHEN a valid user attempts to update a permission by ID,
    THEN the response should reflect the updated permission details if the update is successful,
    EXPECT the response status code to be 200 for successful updates, 404 for missing permissions, and 422 for validation errors.
    """

    permission = PermissionFactory.build()
    db_session.add(permission)
    db_session.flush()
    permission_id = (
        permission.permission_id if permission_exists else MISSING_PERMISSION_ID
    )

    response = client.put(
        f"{BASE_URL}/{permission_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = PermissionSchema.model_validate(response.json())

    assert validated_body.permission_id == permission_id
    assert validated_body.action == request_body["action"]
    assert validated_body.resource == request_body["resource"]
    assert validated_body.description == request_body["description"]
    assert validated_body.modified_by == act_as_admin.user_id


@pytest.mark.usefixtures("act_as_admin")
def test_put_update_permission_conflicting_action_and_resource(
    db_session, client, auth_headers
):
    """
    WHEN a valid user attempts to update a permission with an action and resource
    pair already held by another permission,
    THEN the response should indicate a conflict,
    EXPECT the response to be 409 with a message naming the conflicting fields.
    """

    permission = PermissionFactory.build()
    conflicting_permission = PermissionFactory.build()
    db_session.add_all([permission, conflicting_permission])
    db_session.flush()

    # reuse a value already held by another permission
    request_body = {
        "action": conflicting_permission.action,
        "resource": conflicting_permission.resource,
        "description": permission.description,
    }

    response = client.put(
        f"{BASE_URL}/{permission.permission_id}",
        json=request_body,
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert "Permission already exists" in response.text


# MARK: PATCH tests
@pytest.mark.parametrize(
    "permission_exists, request_body, expected_status_code",
    [
        pytest.param(True, {"description": "Patched"}, 200, id="single-field"),
        pytest.param(
            True,
            {
                "action": "delete",
                "resource": "patched-resource",
                "description": "Patched description",
            },
            200,
            id="multiple-fields",
        ),
        pytest.param(True, {}, 200, id="empty-body"),
        pytest.param(False, {"description": "Patched"}, 404, id="missing-permission"),
        pytest.param(True, {"action": None}, 422, id="null-action"),
        pytest.param(True, {"resource": None}, 422, id="null-resource"),
        pytest.param(True, {"description": None}, 422, id="null-description"),
        pytest.param(True, {"action": "publish"}, 422, id="unknown-action"),
    ],
)
def test_patch_update_permission_by_id(
    db_session,
    client,
    act_as_admin,
    auth_headers,
    permission_exists,
    request_body,
    expected_status_code,
):
    """
    WHEN a valid user attempts to partially update a permission by ID, leaving omitted
    fields untouched,
    THEN the response should reflect the updated permission details if the update is successful,
    EXPECT the response status code to be 200 for successful updates, 404 for missing permissions, and 422 for validation errors.
    """

    permission = PermissionFactory.build()
    db_session.add(permission)
    db_session.flush()
    permission_id = (
        permission.permission_id if permission_exists else MISSING_PERMISSION_ID
    )
    original = {
        "action": permission.action,
        "resource": permission.resource,
        "description": permission.description,
    }

    response = client.patch(
        f"{BASE_URL}/{permission_id}", json=request_body, headers=auth_headers
    )

    assert response.status_code == expected_status_code
    if expected_status_code != 200:
        return

    validated_body = PermissionSchema.model_validate(response.json())
    expected = original | request_body

    assert validated_body.permission_id == permission_id
    assert validated_body.action == expected["action"]
    assert validated_body.resource == expected["resource"]
    assert validated_body.description == expected["description"]
    assert validated_body.modified_by == act_as_admin.user_id


@pytest.mark.usefixtures("act_as_admin")
def test_patch_update_permission_conflicting_action_and_resource(
    db_session, client, auth_headers
):
    """
    WHEN a valid user attempts to patch a permission so that its action and resource
    pair is already held by another permission,
    THEN the response should indicate a conflict,
    EXPECT the response to be 409 with a message naming the conflicting fields.
    """

    permission = PermissionFactory.build()
    conflicting_permission = PermissionFactory.build()
    db_session.add_all([permission, conflicting_permission])
    db_session.flush()

    # reuse a value already held by another permission
    request_body = {"resource": conflicting_permission.resource}

    response = client.patch(
        f"{BASE_URL}/{permission.permission_id}",
        json=request_body,
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert "Permission already exists" in response.text


# MARK: DELETE tests
@pytest.mark.usefixtures("act_as_admin")
def test_delete_permission_by_id(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to delete an existing permission by ID
    THEN the response should indicate successful deletion
    EXPECT the response to be 204
    """

    permission = PermissionFactory.build()
    db_session.add(permission)
    db_session.flush()
    permission_id = permission.permission_id

    response = client.delete(f"{BASE_URL}/{permission_id}", headers=auth_headers)

    assert response.status_code == 204

    # the target permission is only gone if it was the one deleted
    db_permission = db_session.scalars(
        select(Permission).where(Permission.permission_id == permission_id)
    ).one_or_none()

    assert db_permission is None


@pytest.mark.usefixtures("act_as_admin")
def test_delete_non_existing_permission_by_id(client, auth_headers):
    """
    WHEN a valid user attempts to delete a non-existing permission by ID,
    THEN the response should indicate the permission was not found,
    EXPECT the response to be 404
    """

    response = client.delete(
        f"{BASE_URL}/{MISSING_PERMISSION_ID}", headers=auth_headers
    )

    assert response.status_code == 404
    assert "Permission not found" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_delete_existing_permission_by_id_twice(db_session, client, auth_headers):
    """
    WHEN the permission is deleted and then the endpoint is called again
    THEN the first response should indicate successful deletion and the second that the permission was not found
    EXPECT the response to be 204 then 404
    """

    permission = PermissionFactory.build()
    db_session.add(permission)
    db_session.flush()
    permission_id = permission.permission_id

    response = client.delete(f"{BASE_URL}/{permission_id}", headers=auth_headers)

    assert response.status_code == 204

    response = client.delete(f"{BASE_URL}/{permission_id}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.usefixtures("act_as_admin")
def test_delete_permission_assigned_to_role(db_session, client, auth_headers):
    """
    WHEN a permission that is assigned to a role is deleted,
    THEN the deletion should succeed and the permission's assignments should be removed,
    EXPECT the response to be 204 and no role_permissions rows to remain
    """

    role_permission = RolePermissionFactory.build()
    db_session.add(role_permission)
    db_session.flush()
    permission_id = role_permission.permission_id

    response = client.delete(f"{BASE_URL}/{permission_id}", headers=auth_headers)

    assert response.status_code == 204

    # ON DELETE CASCADE happens in the database, so query rather than trust the session
    rows = db_session.scalars(
        select(RolePermission).where(RolePermission.permission_id == permission_id)
    ).all()

    assert rows == []


# MARK: Authorization tests
@pytest.mark.parametrize(
    "method, path, granted_permission, expected_status_code",
    [
        pytest.param("GET", "", AppPermissions.READ__PERMISSIONS, 200, id="get-all"),
        pytest.param("GET", "", AppPermissions.READ__USERS, 403, id="get-all-denied"),
        pytest.param(
            "GET", "/{id}", AppPermissions.READ__PERMISSIONS, 200, id="get-by-id"
        ),
        pytest.param(
            "GET", "/{id}", AppPermissions.READ__USERS, 403, id="get-by-id-denied"
        ),
        pytest.param("POST", "", AppPermissions.CREATE__PERMISSIONS, 201, id="post"),
        pytest.param(
            "POST", "", AppPermissions.READ__PERMISSIONS, 403, id="post-denied"
        ),
        pytest.param("PUT", "/{id}", AppPermissions.UPDATE__PERMISSIONS, 200, id="put"),
        pytest.param(
            "PUT", "/{id}", AppPermissions.READ__PERMISSIONS, 403, id="put-denied"
        ),
        pytest.param(
            "PATCH", "/{id}", AppPermissions.UPDATE__PERMISSIONS, 200, id="patch"
        ),
        pytest.param(
            "PATCH", "/{id}", AppPermissions.READ__PERMISSIONS, 403, id="patch-denied"
        ),
        pytest.param(
            "DELETE", "/{id}", AppPermissions.DELETE__PERMISSIONS, 204, id="delete"
        ),
        pytest.param(
            "DELETE", "/{id}", AppPermissions.READ__PERMISSIONS, 403, id="delete-denied"
        ),
    ],
)
def test_permission_routes_require_matching_permission(
    db_session,
    client,
    act_as_user,
    auth_headers,
    grant_permissions,
    method,
    path,
    granted_permission,
    expected_status_code,
):
    """
    WHEN a user calls a permission endpoint,
    THEN access should depend on holding the permission that endpoint requires,
    EXPECT the success status code with that permission and 403 with any other.
    """

    grant_permissions(act_as_user, [granted_permission])
    permission = PermissionFactory.build()
    db_session.add(permission)
    db_session.flush()

    request_body = {
        "action": "create",
        "resource": "authorization-test",
        "description": "A permission",
    }

    response = client.request(
        method,
        f"{BASE_URL}{path.format(id=permission.permission_id)}",
        json=request_body if method in ("POST", "PUT", "PATCH") else None,
        headers=auth_headers,
    )

    assert response.status_code == expected_status_code
