import uuid

import pytest
from sqlalchemy import select

from app.core.app_permissions import AppPermissions
from app.models.model import Permission, Role, RolePermission
from app.schemas.permission import PermissionSchemaPaginated
from app.schemas.role_permission import RolePermissionSchema
from seeding.factories import PermissionFactory, RoleFactory, RolePermissionFactory

BASE_URL = "/api/v1/roles"
MISSING_ROLE_ID = "a_missing_role"
MISSING_PERMISSION_ID = uuid.UUID(int=0)


def seed_role_permissions(db_session, num_permissions: int = 1) -> RolePermission:
    """
    Seed a new role holding the given number of new permissions, returning the last link
    """
    role = RoleFactory.build()
    role_permissions = [
        RolePermissionFactory.build(role=role) for _ in range(num_permissions)
    ]
    db_session.add_all(role_permissions)
    db_session.flush()
    return role_permissions[-1]


def seed_role_and_permission(db_session) -> tuple[Role, Permission]:
    """
    Seed a new role and a new permission that aren't linked
    """
    role = RoleFactory.build()
    permission = PermissionFactory.build()
    db_session.add_all([role, permission])
    db_session.flush()
    return role, permission


# MARK: GET tests
@pytest.mark.parametrize(
    "num_seed_permissions, page, size, expected_items",
    [
        pytest.param(20, 1, 10, 10, id="default"),
        pytest.param(20, 2, 5, 5, id="second_page"),
        pytest.param(20, 3, 8, 4, id="partial_last_page"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_get_role_permissions_paginated(
    db_session, client, auth_headers, num_seed_permissions, page, size, expected_items
):
    """
    WHEN a valid user requests a paginated list of a role's permissions,
    THEN the response should include the correct number of permissions for the requested page and size,
    EXPECT the response to be 200 and the pagination metadata to be accurate.
    """

    role_id = seed_role_permissions(db_session, num_seed_permissions).role_id

    response = client.get(
        f"{BASE_URL}/{role_id}/permissions?page={page}&size={size}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    validated_body = PermissionSchemaPaginated.model_validate(response.json())

    assert len(validated_body.items) == expected_items
    assert validated_body.total == num_seed_permissions
    assert validated_body.page == page
    assert validated_body.size == size


@pytest.mark.usefixtures("act_as_admin")
def test_get_role_permissions_only_returns_target_role(
    db_session, client, auth_headers
):
    """
    WHEN a valid user requests the permissions of a role and another role holds other permissions,
    THEN the response should only include the target role's permissions,
    EXPECT the response to be 200 with the permission details of the target role.
    """

    role_permission = seed_role_permissions(db_session)
    seed_role_permissions(db_session)
    role_id = role_permission.role_id
    permission = role_permission.permission

    response = client.get(f"{BASE_URL}/{role_id}/permissions", headers=auth_headers)

    assert response.status_code == 200

    validated_body = PermissionSchemaPaginated.model_validate(response.json())

    assert [item.permission_id for item in validated_body.items] == [
        permission.permission_id
    ]
    assert validated_body.items[0].action == permission.action
    assert validated_body.items[0].resource == permission.resource


@pytest.mark.usefixtures("act_as_admin")
def test_get_role_permissions_role_without_permissions(
    db_session, client, auth_headers
):
    """
    WHEN a valid user requests the permissions of a role that holds none,
    THEN the response should be an empty list rather than a missing role,
    EXPECT the response to be 200 with no items.
    """

    role, _ = seed_role_and_permission(db_session)

    response = client.get(
        f"{BASE_URL}/{role.role_id}/permissions", headers=auth_headers
    )

    assert response.status_code == 200

    validated_body = PermissionSchemaPaginated.model_validate(response.json())

    assert validated_body.items == []
    assert validated_body.total == 0


@pytest.mark.usefixtures("act_as_admin")
def test_get_role_permissions_missing_role(client, auth_headers):
    """
    WHEN a valid user requests the permissions of a role that doesn't exist,
    THEN the response should indicate the role was not found,
    EXPECT the response to be 404
    """

    response = client.get(
        f"{BASE_URL}/{MISSING_ROLE_ID}/permissions", headers=auth_headers
    )

    assert response.status_code == 404
    assert "Role not found" in response.text


# MARK: POST tests
def test_post_create_role_permission(db_session, client, act_as_admin, auth_headers):
    """
    WHEN a valid user attempts to assign a permission to a role,
    THEN the response should include the new role permission's details,
    EXPECT the response to be 201 and the row to exist with the acting user as its author.
    """

    role, permission = seed_role_and_permission(db_session)
    role_id = role.role_id
    permission_id = permission.permission_id

    response = client.post(
        f"{BASE_URL}/{role_id}/permissions",
        json={"permissionId": str(permission_id)},
        headers=auth_headers,
    )

    assert response.status_code == 201

    validated_body = RolePermissionSchema.model_validate(response.json())

    assert validated_body.role_id == role_id
    assert validated_body.permission_id == permission_id
    assert validated_body.created_by == act_as_admin.user_id
    assert validated_body.modified_by == act_as_admin.user_id

    db_role_permission = db_session.get(RolePermission, (role_id, permission_id))

    assert db_role_permission is not None


@pytest.mark.parametrize(
    "request_body",
    [
        pytest.param({}, id="invalid-missing-permission-id"),
        pytest.param({"permissionId": None}, id="invalid-null-permission-id"),
        pytest.param({"permissionId": "not-a-uuid"}, id="invalid-malformed-uuid"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_post_create_role_permission_invalid_body(
    db_session, client, auth_headers, request_body
):
    """
    WHEN a valid user attempts to assign a permission with an invalid request body,
    THEN the request should be rejected,
    EXPECT the response to be 422
    """

    role, _ = seed_role_and_permission(db_session)

    response = client.post(
        f"{BASE_URL}/{role.role_id}/permissions",
        json=request_body,
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.usefixtures("act_as_admin")
def test_post_create_role_permission_missing_role(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to assign a permission to a role that doesn't exist,
    THEN the response should indicate the role was not found,
    EXPECT the response to be 404
    """

    _, permission = seed_role_and_permission(db_session)

    response = client.post(
        f"{BASE_URL}/{MISSING_ROLE_ID}/permissions",
        json={"permissionId": str(permission.permission_id)},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "Role not found" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_post_create_role_permission_missing_permission(
    db_session, client, auth_headers
):
    """
    WHEN a valid user attempts to assign a permission that doesn't exist to a role,
    THEN the response should indicate the permission was not found,
    EXPECT the response to be 404
    """

    role, _ = seed_role_and_permission(db_session)

    response = client.post(
        f"{BASE_URL}/{role.role_id}/permissions",
        json={"permissionId": str(MISSING_PERMISSION_ID)},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "Permission not found" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_post_create_role_permission_already_assigned(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to assign a permission the role already holds,
    THEN the response should indicate a conflict,
    EXPECT the response to be 409 and the role to still hold a single row for the permission.
    """

    role_permission = seed_role_permissions(db_session)
    role_id = role_permission.role_id
    permission_id = role_permission.permission_id

    response = client.post(
        f"{BASE_URL}/{role_id}/permissions",
        json={"permissionId": str(permission_id)},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert "Permission already assigned to role" in response.text

    rows = db_session.scalars(
        select(RolePermission).where(RolePermission.role_id == role_id)
    ).all()

    assert len(rows) == 1


# MARK: DELETE tests
@pytest.mark.usefixtures("act_as_admin")
def test_delete_role_permission(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to remove a permission from a role,
    THEN only the link between them should be deleted,
    EXPECT the response to be 204, the row to be gone and the role and permission to remain.
    """

    role_permission = seed_role_permissions(db_session)
    role_id = role_permission.role_id
    permission_id = role_permission.permission_id

    response = client.delete(
        f"{BASE_URL}/{role_id}/permissions/{permission_id}", headers=auth_headers
    )

    assert response.status_code == 204

    db_role_permission = db_session.scalars(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    ).one_or_none()

    assert db_role_permission is None
    assert db_session.get(Role, role_id) is not None
    assert db_session.get(Permission, permission_id) is not None


@pytest.mark.usefixtures("act_as_admin")
def test_delete_role_permission_keeps_other_permissions(
    db_session, client, auth_headers
):
    """
    WHEN a valid user removes one of the permissions a role holds,
    THEN the role's other permissions should remain,
    EXPECT the response to be 204 and one row to remain for the role.
    """

    role_permission = seed_role_permissions(db_session, num_permissions=2)
    role_id = role_permission.role_id
    permission_id = role_permission.permission_id

    response = client.delete(
        f"{BASE_URL}/{role_id}/permissions/{permission_id}", headers=auth_headers
    )

    assert response.status_code == 204

    rows = db_session.scalars(
        select(RolePermission).where(RolePermission.role_id == role_id)
    ).all()

    assert len(rows) == 1
    assert rows[0].permission_id != permission_id


@pytest.mark.usefixtures("act_as_admin")
def test_delete_role_permission_not_assigned(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to remove a permission the role doesn't hold,
    THEN the response should indicate the role permission was not found,
    EXPECT the response to be 404
    """

    role, permission = seed_role_and_permission(db_session)

    response = client.delete(
        f"{BASE_URL}/{role.role_id}/permissions/{permission.permission_id}",
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "Role permission not found" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_delete_role_permission_twice(db_session, client, auth_headers):
    """
    WHEN the role permission is deleted and then the endpoint is called again
    THEN the first response should indicate successful deletion and the second that it was not found
    EXPECT the response to be 204 then 404
    """

    role_permission = seed_role_permissions(db_session)
    url = (
        f"{BASE_URL}/{role_permission.role_id}"
        f"/permissions/{role_permission.permission_id}"
    )

    response = client.delete(url, headers=auth_headers)

    assert response.status_code == 204

    response = client.delete(url, headers=auth_headers)

    assert response.status_code == 404


# MARK: Authorization tests
@pytest.mark.parametrize(
    "method, path, granted_permission, expected_status_code",
    [
        pytest.param(
            "GET",
            "/{role_id}/permissions",
            AppPermissions.READ__ROLE_PERMISSIONS,
            200,
            id="get-all",
        ),
        pytest.param(
            "GET",
            "/{role_id}/permissions",
            AppPermissions.READ__ROLES,
            403,
            id="get-all-denied",
        ),
        pytest.param(
            "POST",
            "/{role_id}/permissions",
            AppPermissions.CREATE__ROLE_PERMISSIONS,
            201,
            id="post",
        ),
        pytest.param(
            "POST",
            "/{role_id}/permissions",
            AppPermissions.READ__ROLE_PERMISSIONS,
            403,
            id="post-denied",
        ),
        pytest.param(
            "DELETE",
            "/{role_id}/permissions/{permission_id}",
            AppPermissions.DELETE__ROLE_PERMISSIONS,
            204,
            id="delete",
        ),
        pytest.param(
            "DELETE",
            "/{role_id}/permissions/{permission_id}",
            AppPermissions.READ__ROLE_PERMISSIONS,
            403,
            id="delete-denied",
        ),
    ],
)
def test_role_permission_routes_require_matching_permission(
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
    WHEN a user calls a role permission endpoint,
    THEN access should depend on holding the permission that endpoint requires,
    EXPECT the success status code with that permission and 403 with any other.
    """

    grant_permissions(act_as_user, [granted_permission])
    role_permission = seed_role_permissions(db_session)
    unassigned_permission = PermissionFactory.build()
    db_session.add(unassigned_permission)
    db_session.flush()

    response = client.request(
        method,
        BASE_URL
        + path.format(
            role_id=role_permission.role_id,
            permission_id=role_permission.permission_id,
        ),
        json=(
            {"permissionId": str(unassigned_permission.permission_id)}
            if method == "POST"
            else None
        ),
        headers=auth_headers,
    )

    assert response.status_code == expected_status_code
