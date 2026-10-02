import pytest
from fastapi_pagination import Params, set_params
from sqlalchemy import select
from sqlalchemy.orm.exc import ObjectDeletedError

from app.models.model import Role, RolePermission, User
from app.repositories.generic import CRUDRepository
from app.schemas.filter_generator import FilterPayload
from app.schemas.order_by_generator import OrderByCondition
from app.utils.exception import NoOrderByColumnsSpecified
from seeding.factories import (
    PermissionFactory,
    RoleFactory,
    RolePermissionFactory,
    UserFactory,
    UserRoleFactory,
)

# every role created here is prefixed so filters never match seeded data
PREFIX = "test-generic"


def where(column: str, operator: str, value) -> FilterPayload:
    return FilterPayload.model_validate(
        {"where": {"column": column, "operator": operator, "value": value}}
    )


def order(column: str, orientation: str = "asc") -> list[OrderByCondition]:
    return [
        OrderByCondition.model_validate({"column": column, "orientation": orientation})
    ]


PREFIXED = where("role_id", "like", f"{PREFIX}-%")


def role_values(suffix: str, **overrides) -> dict:
    return {
        "role_id": f"{PREFIX}-{suffix}",
        "name": f"{PREFIX} {suffix}",
        "description": f"description {suffix}",
        **overrides,
    }


@pytest.fixture
def role_repo(db_session) -> CRUDRepository[Role, Role]:
    return CRUDRepository(db_session, Role)


@pytest.fixture
def roles(db_session) -> list[Role]:
    """Three roles: a, b, c (inserted out of order to make sorting meaningful)."""
    built = [
        RoleFactory.build(**role_values(suffix, description=desc))
        for suffix, desc in [("b", "shared"), ("c", "unique"), ("a", "shared")]
    ]
    db_session.add_all(built)
    db_session.flush()
    return built


@pytest.fixture
def role_permissions(db_session) -> list[RolePermission]:
    """Two role permissions on role 'rp-keep' and one on role 'rp-drop'."""
    keep = RoleFactory.build(**role_values("rp-keep"))
    drop = RoleFactory.build(**role_values("rp-drop"))
    built = [
        RolePermissionFactory.build(
            role=role, permission=PermissionFactory.build(description=desc)
        )
        for role, desc in [(keep, "old"), (keep, "old"), (drop, "old")]
    ]
    db_session.add_all(built)
    db_session.flush()
    return built


def get_roles(db_session) -> list[Role]:
    db_session.expire_all()
    return list(
        db_session.scalars(
            select(Role).where(Role.role_id.like(f"{PREFIX}-%")).order_by(Role.role_id)
        )
    )


# MARK: create_single_item
def test_create_single_item_returns_persisted_item(db_session, role_repo):
    role = role_repo.create_single_item(role_values("new"))

    assert role is not None
    assert role.role_id == f"{PREFIX}-new"
    assert role.name == f"{PREFIX} new"
    # server defaults are populated by the refresh
    assert role.created_at is not None
    assert [r.role_id for r in get_roles(db_session)] == [f"{PREFIX}-new"]


def test_create_single_item_without_commit_is_rolled_back(db_session, role_repo):
    savepoint = db_session.begin_nested()
    role = role_repo.create_single_item(role_values("new"), commit=False)
    assert role is not None
    assert role.created_at is not None

    savepoint.rollback()
    assert get_roles(db_session) == []


# MARK: create_multiple_items
def test_create_multiple_items_returns_all_items(db_session, role_repo):
    created = role_repo.create_multiple_items(
        [role_values("x"), role_values("y"), role_values("z")]
    )

    assert created is not None
    assert sorted(r.role_id for r in created) == [
        f"{PREFIX}-x",
        f"{PREFIX}-y",
        f"{PREFIX}-z",
    ]
    assert len(get_roles(db_session)) == 3


def test_create_multiple_items_without_commit_is_rolled_back(db_session, role_repo):
    savepoint = db_session.begin_nested()
    created = role_repo.create_multiple_items(
        [role_values("x"), role_values("y")], commit=False
    )
    assert created is not None
    assert len(created) == 2

    savepoint.rollback()
    assert get_roles(db_session) == []


# MARK: read_single_item
def test_read_single_item_matches_filter(role_repo, roles):
    role = role_repo.read_single_item(where("role_id", "eq", f"{PREFIX}-c"))

    assert role is roles[1]


@pytest.mark.usefixtures("roles")
def test_read_single_item_returns_none_when_no_match(role_repo):
    assert role_repo.read_single_item(where("role_id", "eq", f"{PREFIX}-nope")) is None


@pytest.mark.parametrize(("orientation", "expected"), [("asc", "a"), ("desc", "b")])
@pytest.mark.usefixtures("roles")
def test_read_single_item_respects_sort_by(role_repo, orientation, expected):
    role = role_repo.read_single_item(
        where("description", "eq", "shared"),
        sort_by=order("role_id", orientation),
    )

    assert role is not None
    assert role.role_id == f"{PREFIX}-{expected}"


def test_read_single_item_with_joins(db_session, roles):
    user = UserFactory.build()
    db_session.add(UserRoleFactory.build(user=user, role=roles[1]))
    db_session.flush()
    user_repo = CRUDRepository(db_session, User)

    found = user_repo.read_single_item(
        where("roles.role_id", "eq", roles[1].role_id), joins=[User.roles]
    )

    assert found is user


# MARK: read_by_pk
def test_read_by_pk_returns_item(role_repo, roles):
    assert role_repo.read_by_pk(f"{PREFIX}-a") is roles[2]


def test_read_by_pk_returns_none_when_missing(role_repo):
    assert role_repo.read_by_pk(f"{PREFIX}-missing") is None


def test_read_by_pk_with_composite_key(db_session, role_permissions):
    repo = CRUDRepository(db_session, RolePermission)
    rp = role_permissions[0]

    assert repo.read_by_pk((rp.role_id, rp.permission_id)) is rp


# MARK: read_multiple_items
@pytest.mark.usefixtures("roles")
def test_read_multiple_items_with_filters_and_sort(role_repo):
    result = role_repo.read_multiple_items(
        filters=PREFIXED, sort_by=order("role_id", "desc")
    )

    assert [r.role_id for r in result] == [
        f"{PREFIX}-c",
        f"{PREFIX}-b",
        f"{PREFIX}-a",
    ]


def test_read_multiple_items_without_sort(role_repo, roles):
    result = role_repo.read_multiple_items(filters=PREFIXED)

    assert sorted(r.role_id for r in result) == sorted(r.role_id for r in roles)


def test_read_multiple_items_without_filters_returns_everything(
    db_session, role_repo, roles
):
    result = role_repo.read_multiple_items()

    all_role_ids = set(db_session.scalars(select(Role.role_id)))
    assert {r.role_id for r in result} == all_role_ids
    assert {r.role_id for r in roles} <= all_role_ids


def test_read_multiple_items_with_joins(db_session, roles):
    users = [UserFactory.build() for _ in range(2)]
    for user in users:
        db_session.add(UserRoleFactory.build(user=user, role=roles[0]))
    db_session.add(UserRoleFactory.build(user=UserFactory.build(), role=roles[1]))
    db_session.flush()
    user_repo = CRUDRepository(db_session, User)

    result = user_repo.read_multiple_items(
        filters=where("roles.role_id", "eq", roles[0].role_id),
        joins=[User.roles],
    )

    assert {u.user_id for u in result} == {u.user_id for u in users}


# MARK: read_paginated_items
def test_read_paginated_items_requires_sort_by(role_repo):
    with pytest.raises(NoOrderByColumnsSpecified):
        role_repo.read_paginated_items(sort_by=[], filters=PREFIXED)


@pytest.mark.usefixtures("roles")
def test_read_paginated_items_returns_requested_page(role_repo):
    with set_params(Params(page=1, size=2)):
        first = role_repo.read_paginated_items(
            sort_by=order("role_id"), filters=PREFIXED
        )
    with set_params(Params(page=2, size=2)):
        second = role_repo.read_paginated_items(
            sort_by=order("role_id"), filters=PREFIXED
        )

    assert first.total == 3
    assert [r.role_id for r in first.items] == [f"{PREFIX}-a", f"{PREFIX}-b"]
    assert [r.role_id for r in second.items] == [f"{PREFIX}-c"]


def test_read_paginated_items_with_joins(db_session, roles):
    users = [UserFactory.build() for _ in range(3)]
    for user in users:
        db_session.add(UserRoleFactory.build(user=user, role=roles[0]))
    db_session.add(UserRoleFactory.build(user=UserFactory.build(), role=roles[1]))
    db_session.flush()
    user_repo = CRUDRepository(db_session, User)

    with set_params(Params(page=1, size=2)):
        page = user_repo.read_paginated_items(
            sort_by=order("email"),
            filters=where("roles.role_id", "eq", roles[0].role_id),
            joins=[User.roles],
        )

    assert page.total == 3
    assert [u.email for u in page.items] == sorted(u.email for u in users)[:2]


# MARK: update_multiple_items_with_same_values
@pytest.mark.usefixtures("roles")
def test_update_same_values_updates_matching_rows(db_session, role_repo):
    updated = role_repo.update_multiple_items_with_same_values(
        where("description", "eq", "shared"), {"description": "changed"}
    )

    assert sorted(r.role_id for r in updated) == [f"{PREFIX}-a", f"{PREFIX}-b"]
    assert {r.role_id: r.description for r in get_roles(db_session)} == {
        f"{PREFIX}-a": "changed",
        f"{PREFIX}-b": "changed",
        f"{PREFIX}-c": "unique",
    }


@pytest.mark.usefixtures("roles")
def test_update_same_values_returns_empty_when_no_match(role_repo):
    updated = role_repo.update_multiple_items_with_same_values(
        where("role_id", "eq", f"{PREFIX}-nope"), {"description": "changed"}
    )

    assert updated == []


@pytest.mark.usefixtures("roles")
def test_update_same_values_without_commit_is_rolled_back(db_session, role_repo):
    savepoint = db_session.begin_nested()
    updated = role_repo.update_multiple_items_with_same_values(
        PREFIXED, {"description": "changed"}, commit=False
    )
    assert len(updated) == 3

    savepoint.rollback()
    assert [r.description for r in get_roles(db_session)] == [
        "shared",
        "shared",
        "unique",
    ]


def test_update_same_values_with_joins_single_pk(db_session, roles):
    user = UserFactory.build(given_name="before")
    other = UserFactory.build(given_name="before")
    db_session.add(UserRoleFactory.build(user=user, role=roles[0]))
    db_session.add(UserRoleFactory.build(user=other, role=roles[1]))
    db_session.flush()
    user_repo = CRUDRepository(db_session, User)

    updated = user_repo.update_multiple_items_with_same_values(
        where("roles.role_id", "eq", roles[0].role_id),
        {"given_name": "after"},
        joins=[User.roles],
    )

    assert [u.user_id for u in updated] == [user.user_id]
    db_session.expire_all()
    assert user.given_name == "after"
    assert other.given_name == "before"


@pytest.mark.usefixtures("role_permissions")
def test_update_same_values_with_joins_composite_pk(db_session):
    repo = CRUDRepository(db_session, RolePermission)
    keep_id = f"{PREFIX}-rp-keep"

    updated = repo.update_multiple_items_with_same_values(
        where("role.role_id", "eq", keep_id),
        {"created_by": None, "modified_by": None},
        joins=[RolePermission.role],
    )

    assert len(updated) == 2
    assert {rp.role_id for rp in updated} == {keep_id}


# MARK: update_multiple_items_with_different_values
@pytest.mark.usefixtures("roles")
def test_update_different_values_updates_each_row(db_session, role_repo):
    role_repo.update_multiple_items_with_different_values(
        None,
        [
            {"role_id": f"{PREFIX}-a", "description": "first"},
            {"role_id": f"{PREFIX}-b", "description": "second"},
        ],
    )

    assert [r.description for r in get_roles(db_session)] == [
        "first",
        "second",
        "unique",
    ]


@pytest.mark.usefixtures("roles")
def test_update_different_values_respects_filters(db_session, role_repo):
    role_repo.update_multiple_items_with_different_values(
        where("description", "eq", "unique"),
        [
            {"role_id": f"{PREFIX}-a", "description": "first"},
            {"role_id": f"{PREFIX}-c", "description": "third"},
        ],
    )

    # role a is excluded by the filter, so only role c changes
    assert [r.description for r in get_roles(db_session)] == [
        "shared",
        "shared",
        "third",
    ]


@pytest.mark.usefixtures("roles")
def test_update_different_values_without_commit_is_rolled_back(db_session, role_repo):
    savepoint = db_session.begin_nested()
    role_repo.update_multiple_items_with_different_values(
        None, [{"role_id": f"{PREFIX}-a", "description": "first"}], commit=False
    )
    assert get_roles(db_session)[0].description == "first"

    savepoint.rollback()
    assert get_roles(db_session)[0].description == "shared"


# MARK: delete_multiple_items
@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_deletes_matching_rows(db_session, role_repo):
    deleted = role_repo.delete_multiple_items(where("description", "eq", "shared"))

    assert len(deleted) == 2
    assert [r.role_id for r in get_roles(db_session)] == [f"{PREFIX}-c"]


@pytest.mark.xfail(
    raises=ObjectDeletedError,
    strict=True,
    reason="commit expires the returned rows, which no longer exist to be reloaded",
)
@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_returned_rows_are_readable_after_commit(role_repo):
    deleted = role_repo.delete_multiple_items(where("description", "eq", "shared"))

    assert sorted(r.role_id for r in deleted) == [f"{PREFIX}-a", f"{PREFIX}-b"]


@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_returned_rows_are_readable_without_commit(role_repo):
    deleted = role_repo.delete_multiple_items(
        where("description", "eq", "shared"), commit=False
    )

    assert sorted(r.role_id for r in deleted) == [f"{PREFIX}-a", f"{PREFIX}-b"]


@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_returns_empty_when_no_match(db_session, role_repo):
    deleted = role_repo.delete_multiple_items(where("role_id", "eq", f"{PREFIX}-x"))

    assert deleted == []
    assert len(get_roles(db_session)) == 3


@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_without_commit_is_rolled_back(db_session, role_repo):
    savepoint = db_session.begin_nested()
    deleted = role_repo.delete_multiple_items(PREFIXED, commit=False)
    assert len(deleted) == 3

    savepoint.rollback()
    assert len(get_roles(db_session)) == 3


def test_delete_multiple_items_with_joins_single_pk(db_session, roles):
    user = UserFactory.build()
    other = UserFactory.build()
    db_session.add(UserRoleFactory.build(user=user, role=roles[0]))
    db_session.add(UserRoleFactory.build(user=other, role=roles[1]))
    db_session.flush()
    user_id, other_id = user.user_id, other.user_id
    user_repo = CRUDRepository(db_session, User)

    deleted = user_repo.delete_multiple_items(
        where("roles.role_id", "eq", roles[0].role_id), joins=[User.roles]
    )

    assert len(deleted) == 1
    db_session.expire_all()
    assert db_session.get(User, user_id) is None
    assert db_session.get(User, other_id) is not None


@pytest.mark.usefixtures("role_permissions")
def test_delete_multiple_items_with_joins_composite_pk(db_session):
    repo = CRUDRepository(db_session, RolePermission)
    drop_id = f"{PREFIX}-rp-drop"

    deleted = repo.delete_multiple_items(
        where("role.role_id", "eq", drop_id), joins=[RolePermission.role]
    )

    assert len(deleted) == 1
    db_session.expire_all()
    remaining = db_session.scalars(
        select(RolePermission.role_id).where(RolePermission.role_id.like(f"{PREFIX}-%"))
    ).all()
    assert remaining == [f"{PREFIX}-rp-keep", f"{PREFIX}-rp-keep"]
