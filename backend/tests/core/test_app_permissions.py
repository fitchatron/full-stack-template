import pytest
from sqlalchemy import and_, select
from app.core.app_permissions import AppPermissions
from app.models.model import Permission


@pytest.mark.parametrize(
    "app_permission, expected_value",
    [
        pytest.param(
            AppPermissions.ASTERISK__ASTERISK,
            "*:*",
            id="asterisk_asterisk",
        ),
        pytest.param(
            AppPermissions.CREATE__ASTERISK,
            "create:*",
            id="create_asterisk",
        ),
        pytest.param(
            AppPermissions.ASTERISK__USERS,
            "*:users",
            id="asterisk_users",
        ),
        pytest.param(
            AppPermissions.CREATE__USERS,
            "create:users",
            id="create_users",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "read:users",
            id="read_users",
        ),
        pytest.param(
            AppPermissions.UPDATE__USERS,
            "update:users",
            id="update_users",
        ),
        pytest.param(
            AppPermissions.DELETE__USERS,
            "delete:users",
            id="delete_users",
        ),
        pytest.param(
            AppPermissions.CREATE__PERMISSIONS,
            "create:permissions",
            id="create_permissions",
        ),
        pytest.param(
            AppPermissions.READ__PERMISSIONS,
            "read:permissions",
            id="read_permissions",
        ),
        pytest.param(
            AppPermissions.UPDATE__PERMISSIONS,
            "update:permissions",
            id="update_permissions",
        ),
        pytest.param(
            AppPermissions.DELETE__PERMISSIONS,
            "delete:permissions",
            id="delete_permissions",
        ),
        pytest.param(
            AppPermissions.CREATE__ROLES,
            "create:roles",
            id="create_roles",
        ),
        pytest.param(
            AppPermissions.READ__ROLES,
            "read:roles",
            id="read_roles",
        ),
        pytest.param(
            AppPermissions.UPDATE__ROLES,
            "update:roles",
            id="update_roles",
        ),
        pytest.param(
            AppPermissions.DELETE__ROLES,
            "delete:roles",
            id="delete_roles",
        ),
        pytest.param(
            AppPermissions.CREATE__ROLE_PERMISSIONS,
            "create:role_permissions",
            id="create_role_permissions",
        ),
        pytest.param(
            AppPermissions.READ__ROLE_PERMISSIONS,
            "read:role_permissions",
            id="read_role_permissions",
        ),
        pytest.param(
            AppPermissions.UPDATE__ROLE_PERMISSIONS,
            "update:role_permissions",
            id="update_role_permissions",
        ),
        pytest.param(
            AppPermissions.DELETE__ROLE_PERMISSIONS,
            "delete:role_permissions",
            id="delete_role_permissions",
        ),
        pytest.param(
            AppPermissions.CREATE__USER_ROLES,
            "create:user_roles",
            id="create_user_roles",
        ),
        pytest.param(
            AppPermissions.READ__USER_ROLES,
            "read:user_roles",
            id="read_user_roles",
        ),
        pytest.param(
            AppPermissions.UPDATE__USER_ROLES,
            "update:user_roles",
            id="update_user_roles",
        ),
        pytest.param(
            AppPermissions.DELETE__USER_ROLES,
            "delete:user_roles",
            id="delete_user_roles",
        ),
    ],
)
def test_get_app_permission_value(app_permission, expected_value):
    assert app_permission.value == expected_value


@pytest.mark.parametrize(
    "app_permission, expected_action, expected_resource",
    [
        # 1. Filter by Department, Order ASC
        pytest.param(
            AppPermissions.ASTERISK__ASTERISK,
            "*",
            "*",
            id="asterisk_asterisk",
        ),
        pytest.param(
            AppPermissions.CREATE__ASTERISK,
            "create",
            "*",
            id="create_asterisk",
        ),
        pytest.param(
            AppPermissions.ASTERISK__USERS,
            "*",
            "users",
            id="asterisk_users",
        ),
        pytest.param(
            AppPermissions.CREATE__USERS,
            "create",
            "users",
            id="create_users",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "read",
            "users",
            id="read_users",
        ),
        pytest.param(
            AppPermissions.UPDATE__USERS,
            "update",
            "users",
            id="update_users",
        ),
        pytest.param(
            AppPermissions.DELETE__USERS,
            "delete",
            "users",
            id="delete_users",
        ),
    ],
)
def test_get_action_resource(app_permission, expected_action, expected_resource):
    action, resource = app_permission.get_action_resource()
    assert action == expected_action
    assert resource == expected_resource


@pytest.mark.parametrize(
    "app_permission, expected_action, expected_resource",
    [
        pytest.param(
            AppPermissions.ASTERISK__ASTERISK,
            "*",
            "*",
            id="asterisk_asterisk",
        ),
        pytest.param(
            AppPermissions.CREATE__ASTERISK,
            "create",
            "*",
            id="create_asterisk",
        ),
        pytest.param(
            AppPermissions.ASTERISK__USERS,
            "*",
            "users",
            id="asterisk_users",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "read",
            "users",
            id="read_users",
        ),
        pytest.param(
            AppPermissions.DELETE__ROLE_PERMISSIONS,
            "delete",
            "role_permissions",
            id="delete_role_permissions",
        ),
    ],
)
def test_convert_to_filter_clause(app_permission, expected_action, expected_resource):
    db_filter = app_permission.to_filter_clause()
    expected_filter = and_(
        Permission.action == expected_action,
        Permission.resource == expected_resource,
    )
    assert db_filter.compare(expected_filter)


@pytest.mark.parametrize(
    "app_permission, expected_action, expected_resource",
    [
        pytest.param(
            AppPermissions.ASTERISK__ASTERISK,
            "*",
            "*",
            id="asterisk_asterisk",
        ),
        pytest.param(
            AppPermissions.CREATE__ASTERISK,
            "create",
            "*",
            id="create_asterisk",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "read",
            "users",
            id="read_users",
        ),
    ],
)
def test_to_granted_by_clause(app_permission, expected_action, expected_resource):
    db_filter = app_permission.to_granted_by_clause()
    expected_filter = and_(
        Permission.action.in_(["*", expected_action]),
        Permission.resource.in_(["*", expected_resource]),
    )
    assert db_filter.compare(expected_filter)


@pytest.mark.parametrize(
    "app_permission, expected_granted_by",
    [
        pytest.param(
            AppPermissions.READ__USERS,
            {"*:*", "*:users", "read:users"},
            id="read_users",
        ),
        pytest.param(
            AppPermissions.CREATE__USERS,
            {"*:*", "create:*", "*:users", "create:users"},
            id="create_users",
        ),
        pytest.param(
            AppPermissions.CREATE__ASTERISK,
            {"*:*", "create:*"},
            id="create_asterisk",
        ),
        pytest.param(
            AppPermissions.ASTERISK__ASTERISK,
            {"*:*"},
            id="asterisk_asterisk",
        ),
    ],
)
def test_to_granted_by_clause_matches_seeded_permissions(
    db_session, app_permission, expected_granted_by
):
    rows = db_session.execute(
        select(Permission.action, Permission.resource).where(
            app_permission.to_granted_by_clause()
        )
    ).all()
    assert {f"{action}:{resource}" for action, resource in rows} == expected_granted_by


@pytest.mark.parametrize("app_permission", list(AppPermissions))
def test_to_granted_by_clause_agrees_with_is_granted_by(db_session, app_permission):
    """The SQL and Python versions of the grant rule must never drift apart."""
    all_permissions = db_session.scalars(select(Permission)).all()
    matched_in_sql = set(
        db_session.scalars(
            select(Permission.permission_id).where(
                app_permission.to_granted_by_clause()
            )
        )
    )
    matched_in_python = {
        p.permission_id
        for p in all_permissions
        if app_permission.is_granted_by(p.action, p.resource)
    }
    assert matched_in_sql == matched_in_python


@pytest.mark.parametrize(
    "app_permission, held_action, held_resource, expected",
    [
        pytest.param(
            AppPermissions.READ__USERS,
            "read",
            "users",
            True,
            id="exact",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "*",
            "users",
            True,
            id="action_wildcard",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "read",
            "*",
            True,
            id="resource_wildcard",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "*",
            "*",
            True,
            id="both_wildcards",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "delete",
            "users",
            False,
            id="wrong_action",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "read",
            "roles",
            False,
            id="wrong_resource",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "*",
            "roles",
            False,
            id="action_wildcard_wrong_resource",
        ),
        pytest.param(
            AppPermissions.READ__USERS,
            "delete",
            "*",
            False,
            id="resource_wildcard_wrong_action",
        ),
        pytest.param(
            AppPermissions.CREATE__ASTERISK,
            "create",
            "users",
            False,
            id="required_wildcard_not_granted_by_specific",
        ),
        pytest.param(
            AppPermissions.CREATE__ASTERISK,
            "create",
            "*",
            True,
            id="required_wildcard_granted_by_same_wildcard",
        ),
        pytest.param(
            AppPermissions.ASTERISK__ASTERISK,
            "*",
            "users",
            False,
            id="required_asterisk_asterisk_not_granted_by_partial_wildcard",
        ),
    ],
)
def test_is_granted_by(app_permission, held_action, held_resource, expected):
    assert app_permission.is_granted_by(held_action, held_resource) is expected
