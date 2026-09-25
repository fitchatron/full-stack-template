from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.core.app_permissions import AppPermissions
from app.core.config import settings
from app.core.security import verify_password
from app.models.model import Permission, RolePermission, User, UserRole


def get_user_permissions(db_session, user: User) -> set[AppPermissions]:
    """Every permission the user holds, across all of their roles."""
    rows = db_session.execute(
        select(Permission.action, Permission.resource)
        .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user.user_id)
    ).all()
    return {AppPermissions(f"{action}:{resource}") for action, resource in rows}


def get_user_roles(db_session, user: User) -> list[UserRole]:
    return list(
        db_session.scalars(select(UserRole).where(UserRole.user_id == user.user_id))
    )


# MARK: act_as_user
def test_act_as_user_is_persisted(db_session, act_as_user):
    user = db_session.scalars(
        select(User).where(
            User.email == "test-act-as-user-is-persisted@test.example.com"
        )
    ).one()
    assert user.user_id == act_as_user.user_id


def test_act_as_user_has_test_password(act_as_user):
    assert verify_password(
        f"{settings.EMAIL_TEST_USER_PASSWORD}{act_as_user.salt}",
        act_as_user.hashed_password,
    )


def test_act_as_user_has_no_roles(db_session, act_as_user):
    assert get_user_roles(db_session, act_as_user) == []
    assert get_user_permissions(db_session, act_as_user) == set()


# MARK: act_as_admin
def test_act_as_admin_has_seeded_admin_role(db_session, act_as_admin):
    user_roles = get_user_roles(db_session, act_as_admin)
    assert [user_role.role_id for user_role in user_roles] == ["admin"]


def test_act_as_admin_has_every_permission(db_session, act_as_admin):
    assert get_user_permissions(db_session, act_as_admin) == set(AppPermissions)


# MARK: grant_permissions
@pytest.mark.parametrize(
    "permissions",
    [
        pytest.param([AppPermissions.READ__USERS], id="single"),
        pytest.param(
            [AppPermissions.READ__USERS, AppPermissions.UPDATE__ROLES],
            id="multiple",
        ),
        pytest.param([AppPermissions.ASTERISK__ASTERISK], id="wildcard"),
        pytest.param([], id="none"),
    ],
)
def test_grant_permissions_grants_exactly_those_permissions(
    db_session, act_as_user, grant_permissions, permissions
):
    grant_permissions(act_as_user, permissions)

    assert get_user_permissions(db_session, act_as_user) == set(permissions)


def test_grant_permissions_with_no_permissions_still_assigns_a_role(
    db_session, act_as_user, grant_permissions
):
    user_role = grant_permissions(act_as_user, [])

    assert [ur.role_id for ur in get_user_roles(db_session, act_as_user)] == [
        user_role.role_id
    ]


def test_grant_permissions_ignores_duplicates(
    db_session, act_as_user, grant_permissions
):
    grant_permissions(
        act_as_user, [AppPermissions.READ__USERS, AppPermissions.READ__USERS]
    )

    assert get_user_permissions(db_session, act_as_user) == {AppPermissions.READ__USERS}


def test_grant_permissions_creates_a_new_role_each_call(
    db_session, act_as_user, grant_permissions
):
    first = grant_permissions(act_as_user, [AppPermissions.READ__USERS])
    second = grant_permissions(act_as_user, [AppPermissions.READ__ROLES])

    assert first.role_id != second.role_id
    assert len(get_user_roles(db_session, act_as_user)) == 2
    assert get_user_permissions(db_session, act_as_user) == {
        AppPermissions.READ__USERS,
        AppPermissions.READ__ROLES,
    }


def test_grant_permissions_passes_through_user_role_fields(
    act_as_user, grant_permissions
):
    start_at = datetime(2020, 1, 1, tzinfo=UTC)
    end_at = start_at + timedelta(days=1)

    user_role = grant_permissions(
        act_as_user, [AppPermissions.READ__USERS], start_at=start_at, end_at=end_at
    )

    assert user_role.start_at == start_at
    assert user_role.end_at == end_at


def test_grant_permissions_raises_for_unseeded_permission(
    db_session, act_as_user, grant_permissions
):
    db_session.execute(
        delete(Permission).where(AppPermissions.DELETE__ROLES.to_filter_clause())
    )

    with pytest.raises(ValueError, match="delete:roles"):
        grant_permissions(
            act_as_user, [AppPermissions.READ__USERS, AppPermissions.DELETE__ROLES]
        )
