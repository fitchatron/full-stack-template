import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.app_permissions import AppPermissions
from app.models.model import Role, User, UserRole
from app.schemas.user_role import UserRoleSchema, UserRoleSchemaPaginated
from seeding.factories import RoleFactory, UserFactory, UserRoleFactory

BASE_URL = "/api/v1/users"
MISSING_USER_ID = uuid.UUID(int=0)
MISSING_ROLE_ID = "a_missing_role"


def seed_user_roles(db_session, num_roles: int = 1) -> UserRole:
    """
    Seed a new user holding the given number of new roles, returning the last link
    """
    user = UserFactory.build()
    user_roles = [UserRoleFactory.build(user=user) for _ in range(num_roles)]
    db_session.add_all(user_roles)
    db_session.flush()
    return user_roles[-1]


def seed_user_role_in_state(db_session, state: str, **kwargs) -> UserRole:
    """
    Seed a new user role that is scheduled, active or expired
    """
    now = datetime.now(UTC)
    start_offset, end_offset = {
        "scheduled": (timedelta(days=1), timedelta(days=2)),
        "active": (timedelta(days=-1), timedelta(days=1)),
        "expired": (timedelta(days=-2), timedelta(days=-1)),
    }[state]
    user_role = UserRoleFactory.build(
        start_at=now + start_offset, end_at=now + end_offset, **kwargs
    )
    db_session.add(user_role)
    db_session.flush()
    return user_role


def seed_user_and_role(db_session) -> tuple[User, Role]:
    """
    Seed a new user and a new role that aren't linked
    """
    user = UserFactory.build()
    role = RoleFactory.build()
    db_session.add_all([user, role])
    db_session.flush()
    return user, role


# MARK: GET tests
@pytest.mark.parametrize(
    "num_seed_roles, page, size, expected_items",
    [
        pytest.param(20, 1, 10, 10, id="default"),
        pytest.param(20, 2, 5, 5, id="second_page"),
        pytest.param(20, 3, 8, 4, id="partial_last_page"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_get_user_roles_paginated(
    db_session, client, auth_headers, num_seed_roles, page, size, expected_items
):
    """
    WHEN a valid user requests a paginated list of a user's roles,
    THEN the response should include the correct number of roles for the requested page and size,
    EXPECT the response to be 200 and the pagination metadata to be accurate.
    """

    user_id = seed_user_roles(db_session, num_seed_roles).user_id

    response = client.get(
        f"{BASE_URL}/{user_id}/roles?page={page}&size={size}",
        headers=auth_headers,
    )

    assert response.status_code == 200

    validated_body = UserRoleSchemaPaginated.model_validate(response.json())

    assert len(validated_body.items) == expected_items
    assert validated_body.total == num_seed_roles
    assert validated_body.page == page
    assert validated_body.size == size


@pytest.mark.usefixtures("act_as_admin")
def test_get_user_roles_only_returns_target_user(db_session, client, auth_headers):
    """
    WHEN a valid user requests the roles of a user and another user holds other roles,
    THEN the response should only include the target user's roles,
    EXPECT the response to be 200 with the user role details of the target user.
    """

    user_role = seed_user_roles(db_session)
    seed_user_roles(db_session)

    response = client.get(f"{BASE_URL}/{user_role.user_id}/roles", headers=auth_headers)

    assert response.status_code == 200

    validated_body = UserRoleSchemaPaginated.model_validate(response.json())

    assert [item.user_role_id for item in validated_body.items] == [
        user_role.user_role_id
    ]
    assert validated_body.items[0].role_id == user_role.role_id
    assert validated_body.items[0].start_at == user_role.start_at
    assert validated_body.items[0].end_at == user_role.end_at


@pytest.mark.usefixtures("act_as_admin")
def test_get_user_roles_includes_inactive_roles(db_session, client, auth_headers):
    """
    WHEN a valid user requests the roles of a user whose role has expired,
    THEN the response should still include the expired role,
    EXPECT the response to be 200 with the expired user role.
    """

    now = datetime.now(UTC)
    user_role = UserRoleFactory.build(
        start_at=now - timedelta(days=2), end_at=now - timedelta(days=1)
    )
    db_session.add(user_role)
    db_session.flush()

    response = client.get(f"{BASE_URL}/{user_role.user_id}/roles", headers=auth_headers)

    assert response.status_code == 200

    validated_body = UserRoleSchemaPaginated.model_validate(response.json())

    assert [item.user_role_id for item in validated_body.items] == [
        user_role.user_role_id
    ]


@pytest.mark.usefixtures("act_as_admin")
def test_get_user_roles_user_without_roles(db_session, client, auth_headers):
    """
    WHEN a valid user requests the roles of a user that holds none,
    THEN the response should be an empty list rather than a missing user,
    EXPECT the response to be 200 with no items.
    """

    user, _ = seed_user_and_role(db_session)

    response = client.get(f"{BASE_URL}/{user.user_id}/roles", headers=auth_headers)

    assert response.status_code == 200

    validated_body = UserRoleSchemaPaginated.model_validate(response.json())

    assert validated_body.items == []
    assert validated_body.total == 0


@pytest.mark.usefixtures("act_as_admin")
def test_get_user_roles_missing_user(client, auth_headers):
    """
    WHEN a valid user requests the roles of a user that doesn't exist,
    THEN the response should indicate the user was not found,
    EXPECT the response to be 404
    """

    response = client.get(f"{BASE_URL}/{MISSING_USER_ID}/roles", headers=auth_headers)

    assert response.status_code == 404
    assert "User not found" in response.text


# MARK: POST tests
def test_post_create_user_role(db_session, client, act_as_admin, auth_headers):
    """
    WHEN a valid user attempts to assign a role to a user without specifying dates,
    THEN the response should include the new user role with the default dates,
    EXPECT the response to be 201 and the row to exist with the acting user as its author.
    """

    user, role = seed_user_and_role(db_session)
    user_id = user.user_id
    role_id = role.role_id

    response = client.post(
        f"{BASE_URL}/{user_id}/roles",
        json={"roleId": role_id},
        headers=auth_headers,
    )

    assert response.status_code == 201

    validated_body = UserRoleSchema.model_validate(response.json())

    assert validated_body.user_id == user_id
    assert validated_body.role_id == role_id
    assert validated_body.end_at > validated_body.start_at
    assert validated_body.created_by == act_as_admin.user_id
    assert validated_body.modified_by == act_as_admin.user_id

    db_user_role = db_session.get(UserRole, validated_body.user_role_id)

    assert db_user_role is not None


@pytest.mark.parametrize(
    "start_at, end_at",
    [
        pytest.param(
            datetime(2030, 1, 1, tzinfo=UTC),
            datetime(2030, 6, 1, tzinfo=UTC),
            id="start-before-end",
        ),
        pytest.param(
            datetime(2030, 1, 1, tzinfo=UTC),
            datetime(2030, 1, 1, tzinfo=UTC),
            id="start-equals-end",
        ),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_post_create_user_role_with_dates(
    db_session, client, auth_headers, start_at, end_at
):
    """
    WHEN a valid user attempts to assign a role to a user for a specific period,
    THEN the user role should be created with that period,
    EXPECT the response to be 201 and the dates to match the request.
    """

    user, role = seed_user_and_role(db_session)

    response = client.post(
        f"{BASE_URL}/{user.user_id}/roles",
        json={
            "roleId": role.role_id,
            "startAt": start_at.isoformat(),
            "endAt": end_at.isoformat(),
        },
        headers=auth_headers,
    )

    assert response.status_code == 201

    validated_body = UserRoleSchema.model_validate(response.json())

    assert validated_body.start_at == start_at
    assert validated_body.end_at == end_at


@pytest.mark.parametrize(
    "request_body",
    [
        pytest.param({}, id="invalid-missing-role-id"),
        pytest.param({"roleId": None}, id="invalid-null-role-id"),
        pytest.param({"roleId": "admin", "startAt": None}, id="invalid-null-start-at"),
        pytest.param({"roleId": "admin", "endAt": None}, id="invalid-null-end-at"),
        pytest.param(
            {"roleId": "admin", "startAt": "not-a-date"}, id="invalid-malformed-date"
        ),
        pytest.param(
            {"roleId": "admin", "startAt": "2030-01-01T00:00:00"},
            id="invalid-naive-date",
        ),
        pytest.param(
            {
                "roleId": "admin",
                "startAt": "2030-06-01T00:00:00Z",
                "endAt": "2030-01-01T00:00:00Z",
            },
            id="invalid-end-before-start",
        ),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_post_create_user_role_invalid_body(
    db_session, client, auth_headers, request_body
):
    """
    WHEN a valid user attempts to assign a role with an invalid request body,
    THEN the request should be rejected,
    EXPECT the response to be 422
    """

    user, _ = seed_user_and_role(db_session)

    response = client.post(
        f"{BASE_URL}/{user.user_id}/roles",
        json=request_body,
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.usefixtures("act_as_admin")
def test_post_create_user_role_missing_user(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to assign a role to a user that doesn't exist,
    THEN the response should indicate the user was not found,
    EXPECT the response to be 404
    """

    _, role = seed_user_and_role(db_session)

    response = client.post(
        f"{BASE_URL}/{MISSING_USER_ID}/roles",
        json={"roleId": role.role_id},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "User not found" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_post_create_user_role_missing_role(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to assign a role that doesn't exist to a user,
    THEN the response should indicate the role was not found,
    EXPECT the response to be 404
    """

    user, _ = seed_user_and_role(db_session)

    response = client.post(
        f"{BASE_URL}/{user.user_id}/roles",
        json={"roleId": MISSING_ROLE_ID},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "Role not found" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_post_create_user_role_end_before_default_start(
    db_session, client, auth_headers
):
    """
    WHEN a valid user omits start_at and sends an end_at before the default start of now,
    THEN the request should be rejected,
    EXPECT the response to be 400
    """

    user, role = seed_user_and_role(db_session)

    response = client.post(
        f"{BASE_URL}/{user.user_id}/roles",
        json={"roleId": role.role_id, "endAt": "2020-01-01T00:00:00Z"},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "start_at cannot be later than end_at" in response.text


@pytest.mark.parametrize(
    "state, start_offset, end_offset, expected_status_code",
    [
        pytest.param("active", -1, 1, 409, id="same-period"),
        pytest.param("active", -3, -0.5, 409, id="overlaps-start"),
        pytest.param("active", 0.5, 3, 409, id="overlaps-end"),
        pytest.param("active", -3, 3, 409, id="contains-existing"),
        pytest.param("active", -0.5, 0.5, 409, id="within-existing"),
        pytest.param("active", 2, 3, 201, id="after-existing"),
        pytest.param("active", -3, -2, 201, id="before-existing"),
        pytest.param("expired", 0, 1, 201, id="renews-expired"),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_post_create_user_role_overlapping_period(
    db_session,
    client,
    auth_headers,
    state,
    start_offset,
    end_offset,
    expected_status_code,
):
    """
    WHEN a valid user attempts to assign a role the user holds in another period,
    THEN the role should only be assigned if the periods don't overlap,
    EXPECT the response to be 409 when they overlap and 201 otherwise.
    """

    user_role = seed_user_role_in_state(db_session, state)
    user_id = user_role.user_id
    now = datetime.now(UTC)

    response = client.post(
        f"{BASE_URL}/{user_id}/roles",
        json={
            "roleId": user_role.role_id,
            "startAt": (now + timedelta(days=start_offset)).isoformat(),
            "endAt": (now + timedelta(days=end_offset)).isoformat(),
        },
        headers=auth_headers,
    )

    assert response.status_code == expected_status_code

    rows = db_session.scalars(select(UserRole).where(UserRole.user_id == user_id)).all()

    assert len(rows) == (2 if expected_status_code == 201 else 1)


@pytest.mark.usefixtures("act_as_admin")
def test_post_create_user_role_overlapping_period_of_other_role(
    db_session, client, auth_headers
):
    """
    WHEN a valid user assigns a role for a period where the user holds a different role,
    THEN the user should hold both roles at once,
    EXPECT the response to be 201
    """

    user_role = seed_user_role_in_state(db_session, "active")
    role = RoleFactory.build()
    db_session.add(role)
    db_session.flush()

    response = client.post(
        f"{BASE_URL}/{user_role.user_id}/roles",
        json={"roleId": role.role_id},
        headers=auth_headers,
    )

    assert response.status_code == 201


def test_post_create_user_role_for_self(db_session, client, act_as_admin, auth_headers):
    """
    WHEN a user attempts to assign a role to themselves,
    THEN the response should indicate forbidden action,
    EXPECT the response to be 403 and no new row to exist.
    """

    _, role = seed_user_and_role(db_session)
    role_id = role.role_id

    response = client.post(
        f"{BASE_URL}/{act_as_admin.user_id}/roles",
        json={"roleId": role_id},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert "Users cannot change their own roles" in response.text

    rows = db_session.scalars(select(UserRole).where(UserRole.role_id == role_id)).all()

    assert rows == []


# MARK: PATCH tests
@pytest.mark.parametrize(
    "end_offset",
    [
        pytest.param(timedelta(days=30), id="longer"),
        pytest.param(timedelta(hours=1), id="shorter"),
    ],
)
def test_patch_active_user_role_end_at(
    db_session, client, act_as_admin, auth_headers, end_offset
):
    """
    WHEN a valid user changes the end date of an active user role and it stays active,
    THEN only the end date should change,
    EXPECT the response to be 200 with the new end date and the acting user as modifier.
    """

    user_role = seed_user_role_in_state(db_session, "active")
    start_at = user_role.start_at
    end_at = datetime.now(UTC) + end_offset

    response = client.patch(
        f"{BASE_URL}/{user_role.user_id}/roles/{user_role.user_role_id}",
        json={"endAt": end_at.isoformat()},
        headers=auth_headers,
    )

    assert response.status_code == 200

    validated_body = UserRoleSchema.model_validate(response.json())

    assert validated_body.end_at == end_at
    assert validated_body.start_at == start_at
    assert validated_body.modified_by == act_as_admin.user_id


@pytest.mark.usefixtures("act_as_admin")
def test_patch_active_user_role_end_at_in_past(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to backdate the end of an active user role,
    THEN the request should be rejected,
    EXPECT the response to be 400 and the end date to be unchanged.
    """

    user_role = seed_user_role_in_state(db_session, "active")
    user_role_id = user_role.user_role_id
    end_at = user_role.end_at

    response = client.patch(
        f"{BASE_URL}/{user_role.user_id}/roles/{user_role_id}",
        json={"endAt": (datetime.now(UTC) - timedelta(minutes=1)).isoformat()},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "end_at cannot be in the past" in response.text
    assert db_session.get(UserRole, user_role_id).end_at == end_at


@pytest.mark.usefixtures("act_as_admin")
def test_patch_active_user_role_start_at(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to change the start date of an active user role,
    THEN the request should be rejected,
    EXPECT the response to be 409 and the start date to be unchanged.
    """

    user_role = seed_user_role_in_state(db_session, "active")
    user_role_id = user_role.user_role_id
    start_at = user_role.start_at

    response = client.patch(
        f"{BASE_URL}/{user_role.user_id}/roles/{user_role_id}",
        json={"startAt": (datetime.now(UTC) + timedelta(hours=1)).isoformat()},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert "Active user roles cannot change their start date" in response.text
    assert db_session.get(UserRole, user_role_id).start_at == start_at


@pytest.mark.parametrize(
    "request_body",
    [
        pytest.param({"roleId": "admin"}, id="invalid-role-id"),
        pytest.param({"userId": str(MISSING_USER_ID)}, id="invalid-user-id"),
        pytest.param({"startAt": None}, id="invalid-null-start-at"),
        pytest.param({"endAt": None}, id="invalid-null-end-at"),
        pytest.param({"endAt": "2030-01-01T00:00:00"}, id="invalid-naive-date"),
        pytest.param(
            {"startAt": "2030-06-01T00:00:00Z", "endAt": "2030-01-01T00:00:00Z"},
            id="invalid-start-after-end",
        ),
    ],
)
@pytest.mark.parametrize("state", ["scheduled", "active"])
@pytest.mark.usefixtures("act_as_admin")
def test_patch_user_role_invalid_body(
    db_session, client, auth_headers, state, request_body
):
    """
    WHEN a valid user attempts to patch a user role with an invalid request body,
    THEN the request should be rejected rather than the fields being ignored,
    EXPECT the response to be 422
    """

    user_role = seed_user_role_in_state(db_session, state)

    response = client.patch(
        f"{BASE_URL}/{user_role.user_id}/roles/{user_role.user_role_id}",
        json=request_body,
        headers=auth_headers,
    )

    assert response.status_code == 422


@pytest.mark.usefixtures("act_as_admin")
def test_patch_scheduled_user_role_dates(db_session, client, auth_headers):
    """
    WHEN a valid user changes both dates of a scheduled user role,
    THEN both dates should change,
    EXPECT the response to be 200 with the new dates.
    """

    user_role = seed_user_role_in_state(db_session, "scheduled")
    start_at = datetime.now(UTC) + timedelta(days=10)
    end_at = start_at + timedelta(days=10)

    response = client.patch(
        f"{BASE_URL}/{user_role.user_id}/roles/{user_role.user_role_id}",
        json={"startAt": start_at.isoformat(), "endAt": end_at.isoformat()},
        headers=auth_headers,
    )

    assert response.status_code == 200

    validated_body = UserRoleSchema.model_validate(response.json())

    assert validated_body.start_at == start_at
    assert validated_body.end_at == end_at


@pytest.mark.parametrize(
    "field, offset, expected_detail",
    [
        pytest.param(
            "startAt",
            timedelta(days=-1),
            "start_at cannot be in the past",
            id="start-in-past",
        ),
        pytest.param(
            "startAt",
            timedelta(days=5),
            "start_at cannot be later than end_at",
            id="start-after-stored-end",
        ),
        pytest.param(
            "endAt",
            timedelta(hours=1),
            "start_at cannot be later than end_at",
            id="end-before-stored-start",
        ),
    ],
)
@pytest.mark.usefixtures("act_as_admin")
def test_patch_scheduled_user_role_invalid_dates(
    db_session, client, auth_headers, field, offset, expected_detail
):
    """
    WHEN a valid user sends a single date that doesn't fit the scheduled user role,
    THEN the request should be rejected,
    EXPECT the response to be 400
    """

    user_role = seed_user_role_in_state(db_session, "scheduled")

    response = client.patch(
        f"{BASE_URL}/{user_role.user_id}/roles/{user_role.user_role_id}",
        json={field: (datetime.now(UTC) + offset).isoformat()},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert expected_detail in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_patch_expired_user_role(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to change an expired user role,
    THEN the request should be rejected,
    EXPECT the response to be 409 and the end date to be unchanged.
    """

    user_role = seed_user_role_in_state(db_session, "expired")
    user_role_id = user_role.user_role_id
    end_at = user_role.end_at

    response = client.patch(
        f"{BASE_URL}/{user_role.user_id}/roles/{user_role_id}",
        json={"endAt": (datetime.now(UTC) + timedelta(days=1)).isoformat()},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert "Expired user roles cannot be changed" in response.text
    assert db_session.get(UserRole, user_role_id).end_at == end_at


@pytest.mark.usefixtures("act_as_admin")
def test_patch_user_role_overlapping_period(db_session, client, auth_headers):
    """
    WHEN a valid user extends a user role into a later period of the same role,
    THEN the request should be rejected,
    EXPECT the response to be 409
    """

    active = seed_user_role_in_state(db_session, "active")
    seed_user_role_in_state(db_session, "scheduled", user=active.user, role=active.role)

    response = client.patch(
        f"{BASE_URL}/{active.user_id}/roles/{active.user_role_id}",
        json={"endAt": (datetime.now(UTC) + timedelta(days=5)).isoformat()},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert "User already holds this role during this period" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_patch_user_role_of_other_user(db_session, client, auth_headers):
    """
    WHEN a valid user patches a user role through the path of a different user,
    THEN the response should indicate the user role was not found,
    EXPECT the response to be 404
    """

    user_role = seed_user_role_in_state(db_session, "active")
    other_user, _ = seed_user_and_role(db_session)

    response = client.patch(
        f"{BASE_URL}/{other_user.user_id}/roles/{user_role.user_role_id}",
        json={"endAt": (datetime.now(UTC) + timedelta(days=5)).isoformat()},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert "User role not found" in response.text


def test_patch_user_role_for_self(db_session, client, act_as_admin, auth_headers):
    """
    WHEN a user attempts to change one of their own user roles,
    THEN the response should indicate forbidden action,
    EXPECT the response to be 403
    """

    user_role = db_session.scalars(
        select(UserRole).where(UserRole.user_id == act_as_admin.user_id)
    ).one()

    response = client.patch(
        f"{BASE_URL}/{act_as_admin.user_id}/roles/{user_role.user_role_id}",
        json={"endAt": (datetime.now(UTC) + timedelta(days=5)).isoformat()},
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert "Users cannot change their own roles" in response.text


# MARK: DELETE tests
def test_delete_active_user_role(db_session, client, act_as_admin, auth_headers):
    """
    WHEN a valid user revokes an active user role,
    THEN the user role should end now and be kept for audit,
    EXPECT the response to be 204 and the row to remain with an end date of now.
    """

    user_role = seed_user_role_in_state(db_session, "active")
    user_role_id = user_role.user_role_id
    before_request = datetime.now(UTC)

    response = client.delete(
        f"{BASE_URL}/{user_role.user_id}/roles/{user_role_id}", headers=auth_headers
    )

    assert response.status_code == 204

    db_user_role = db_session.get(UserRole, user_role_id)

    assert db_user_role is not None
    assert before_request <= db_user_role.end_at <= datetime.now(UTC)
    assert db_user_role.modified_by == act_as_admin.user_id


@pytest.mark.usefixtures("act_as_admin")
def test_delete_scheduled_user_role(db_session, client, auth_headers):
    """
    WHEN a valid user revokes a scheduled user role,
    THEN the user role should be deleted since it never granted access,
    EXPECT the response to be 204, the row to be gone and the user and role to remain.
    """

    user_role = seed_user_role_in_state(db_session, "scheduled")
    user_role_id = user_role.user_role_id
    user_id = user_role.user_id
    role_id = user_role.role_id

    response = client.delete(
        f"{BASE_URL}/{user_id}/roles/{user_role_id}", headers=auth_headers
    )

    assert response.status_code == 204

    db_user_role = db_session.scalars(
        select(UserRole).where(UserRole.user_role_id == user_role_id)
    ).one_or_none()

    assert db_user_role is None
    assert db_session.get(User, user_id) is not None
    assert db_session.get(Role, role_id) is not None


@pytest.mark.usefixtures("act_as_admin")
def test_delete_expired_user_role(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to revoke an expired user role,
    THEN the request should be rejected,
    EXPECT the response to be 409 and the row to be unchanged.
    """

    user_role = seed_user_role_in_state(db_session, "expired")
    user_role_id = user_role.user_role_id
    end_at = user_role.end_at

    response = client.delete(
        f"{BASE_URL}/{user_role.user_id}/roles/{user_role_id}", headers=auth_headers
    )

    assert response.status_code == 409
    assert "Expired user roles cannot be changed" in response.text
    assert db_session.get(UserRole, user_role_id).end_at == end_at


@pytest.mark.usefixtures("act_as_admin")
def test_delete_user_role_with_same_role_in_another_period(
    db_session, client, auth_headers
):
    """
    WHEN a valid user revokes a user role and the user holds the same role in another period,
    THEN only the targeted row should change,
    EXPECT the response to be 204 and the other row to be unchanged.
    """

    active = seed_user_role_in_state(db_session, "active")
    expired = seed_user_role_in_state(
        db_session, "expired", user=active.user, role=active.role
    )
    expired_id = expired.user_role_id
    expired_end_at = expired.end_at

    response = client.delete(
        f"{BASE_URL}/{active.user_id}/roles/{active.user_role_id}",
        headers=auth_headers,
    )

    assert response.status_code == 204
    assert db_session.get(UserRole, expired_id).end_at == expired_end_at


@pytest.mark.usefixtures("act_as_admin")
def test_delete_missing_user_role(db_session, client, auth_headers):
    """
    WHEN a valid user attempts to revoke a user role that doesn't exist,
    THEN the response should indicate the user role was not found,
    EXPECT the response to be 404
    """

    user, _ = seed_user_and_role(db_session)

    response = client.delete(
        f"{BASE_URL}/{user.user_id}/roles/{MISSING_USER_ID}", headers=auth_headers
    )

    assert response.status_code == 404
    assert "User role not found" in response.text


@pytest.mark.usefixtures("act_as_admin")
def test_delete_user_role_of_other_user(db_session, client, auth_headers):
    """
    WHEN a valid user revokes a user role through the path of a different user,
    THEN the response should indicate the user role was not found,
    EXPECT the response to be 404 and the user role to be unchanged.
    """

    user_role = seed_user_role_in_state(db_session, "active")
    user_role_id = user_role.user_role_id
    end_at = user_role.end_at
    other_user, _ = seed_user_and_role(db_session)

    response = client.delete(
        f"{BASE_URL}/{other_user.user_id}/roles/{user_role_id}", headers=auth_headers
    )

    assert response.status_code == 404
    assert db_session.get(UserRole, user_role_id).end_at == end_at


@pytest.mark.usefixtures("act_as_admin")
def test_delete_user_role_twice(db_session, client, auth_headers):
    """
    WHEN an active user role is revoked and then the endpoint is called again
    THEN the first response should indicate success and the second that it has expired
    EXPECT the response to be 204 then 409
    """

    user_role = seed_user_role_in_state(db_session, "active")
    url = f"{BASE_URL}/{user_role.user_id}/roles/{user_role.user_role_id}"

    response = client.delete(url, headers=auth_headers)

    assert response.status_code == 204

    response = client.delete(url, headers=auth_headers)

    assert response.status_code == 409


def test_delete_user_role_for_self(db_session, client, act_as_admin, auth_headers):
    """
    WHEN a user attempts to revoke one of their own roles,
    THEN the response should indicate forbidden action,
    EXPECT the response to be 403 and the role to still be assigned.
    """

    user_id = act_as_admin.user_id
    user_role = db_session.scalars(
        select(UserRole).where(UserRole.user_id == user_id)
    ).one()
    user_role_id = user_role.user_role_id
    end_at = user_role.end_at

    response = client.delete(
        f"{BASE_URL}/{user_id}/roles/{user_role_id}", headers=auth_headers
    )

    assert response.status_code == 403
    assert "Users cannot change their own roles" in response.text
    assert db_session.get(UserRole, user_role_id).end_at == end_at


# MARK: Model tests
def test_user_role_check_constraint_rejects_start_after_end(db_session):
    """
    WHEN a user role is written directly with a start date later than its end date,
    THEN the database should reject it,
    EXPECT an integrity error from the check constraint.
    """

    now = datetime.now(UTC)
    user_role = UserRoleFactory.build(start_at=now, end_at=now - timedelta(days=1))

    with pytest.raises(IntegrityError, match="ck__user_roles"):
        with db_session.begin_nested():
            db_session.add(user_role)
            db_session.flush()


# MARK: Authorization tests
@pytest.mark.parametrize(
    "method, path, granted_permission, expected_status_code",
    [
        pytest.param(
            "GET",
            "/{user_id}/roles",
            AppPermissions.READ__USER_ROLES,
            200,
            id="get-all",
        ),
        pytest.param(
            "GET",
            "/{user_id}/roles",
            AppPermissions.READ__USERS,
            403,
            id="get-all-denied",
        ),
        pytest.param(
            "POST",
            "/{user_id}/roles",
            AppPermissions.CREATE__USER_ROLES,
            201,
            id="post",
        ),
        pytest.param(
            "POST",
            "/{user_id}/roles",
            AppPermissions.READ__USER_ROLES,
            403,
            id="post-denied",
        ),
        pytest.param(
            "PATCH",
            "/{user_id}/roles/{user_role_id}",
            AppPermissions.UPDATE__USER_ROLES,
            200,
            id="patch",
        ),
        pytest.param(
            "PATCH",
            "/{user_id}/roles/{user_role_id}",
            AppPermissions.READ__USER_ROLES,
            403,
            id="patch-denied",
        ),
        pytest.param(
            "DELETE",
            "/{user_id}/roles/{user_role_id}",
            AppPermissions.DELETE__USER_ROLES,
            204,
            id="delete",
        ),
        pytest.param(
            "DELETE",
            "/{user_id}/roles/{user_role_id}",
            AppPermissions.READ__USER_ROLES,
            403,
            id="delete-denied",
        ),
    ],
)
def test_user_role_routes_require_matching_permission(
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
    WHEN a user calls a user role endpoint,
    THEN access should depend on holding the permission that endpoint requires,
    EXPECT the success status code with that permission and 403 with any other.
    """

    grant_permissions(act_as_user, [granted_permission])
    user_role = seed_user_roles(db_session)
    unassigned_role = RoleFactory.build()
    db_session.add(unassigned_role)
    db_session.flush()

    request_bodies = {
        "POST": {"roleId": unassigned_role.role_id},
        "PATCH": {"endAt": (datetime.now(UTC) + timedelta(days=5)).isoformat()},
    }

    response = client.request(
        method,
        BASE_URL
        + path.format(user_id=user_role.user_id, user_role_id=user_role.user_role_id),
        json=request_bodies.get(method),
        headers=auth_headers,
    )

    assert response.status_code == expected_status_code
