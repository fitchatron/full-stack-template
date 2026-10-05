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
    # GIVEN no roles exist yet
    # WHEN a single role is created (default commit=True)
    role = role_repo.create_single_item(role_values("new"))

    # THEN the returned object reflects the input plus server-generated
    # defaults (populated by the post-commit refresh), and the row is
    # actually persisted -- visible to a fresh query, not just the identity map
    assert role is not None
    assert role.role_id == f"{PREFIX}-new"
    assert role.name == f"{PREFIX} new"
    # server defaults are populated by the refresh
    assert role.created_at is not None
    assert [r.role_id for r in get_roles(db_session)] == [f"{PREFIX}-new"]


def test_create_single_item_without_commit_is_rolled_back(db_session, role_repo):
    # GIVEN an open savepoint
    savepoint = db_session.begin_nested()
    # WHEN a role is created with commit=False
    role = role_repo.create_single_item(role_values("new"), commit=False)
    # THEN the object is usable within the transaction (flushed, so server
    # defaults are already populated) ...
    assert role is not None
    assert role.created_at is not None

    # ... but once the savepoint is rolled back, nothing was ever durably
    # written -- commit=False means the caller owns the transaction boundary
    savepoint.rollback()
    assert get_roles(db_session) == []


# MARK: create_multiple_items
def test_create_multiple_items_returns_all_items(db_session, role_repo):
    # GIVEN no roles exist yet
    # WHEN three roles are created in one call
    created = role_repo.create_multiple_items(
        [role_values("x"), role_values("y"), role_values("z")]
    )

    # THEN all three are returned and persisted
    assert created is not None
    assert sorted(r.role_id for r in created) == [
        f"{PREFIX}-x",
        f"{PREFIX}-y",
        f"{PREFIX}-z",
    ]
    assert len(get_roles(db_session)) == 3


def test_create_multiple_items_without_commit_is_rolled_back(db_session, role_repo):
    # GIVEN an open savepoint
    savepoint = db_session.begin_nested()
    # WHEN two roles are created with commit=False
    created = role_repo.create_multiple_items(
        [role_values("x"), role_values("y")], commit=False
    )
    assert created is not None
    assert len(created) == 2

    # THEN rolling back the savepoint leaves no trace of them
    savepoint.rollback()
    assert get_roles(db_session) == []


# MARK: read_single_item
def test_read_single_item_matches_filter(role_repo, roles):
    # GIVEN roles a, b, c
    # WHEN reading a single item filtered by role_id == c
    role = role_repo.read_single_item(where("role_id", "eq", f"{PREFIX}-c"))

    # THEN the exact same ORM instance already in the session's identity map
    # is returned (roles[1] is role "c")
    assert role is roles[1]


@pytest.mark.usefixtures("roles")
def test_read_single_item_returns_none_when_no_match(role_repo):
    # GIVEN roles a, b, c exist
    # WHEN reading a single item filtered by a role_id that doesn't exist
    # THEN None is returned rather than raising
    assert role_repo.read_single_item(where("role_id", "eq", f"{PREFIX}-nope")) is None


@pytest.mark.parametrize(("orientation", "expected"), [("asc", "a"), ("desc", "b")])
@pytest.mark.usefixtures("roles")
def test_read_single_item_respects_sort_by(role_repo, orientation, expected):
    # GIVEN roles a and b both have description "shared" (role c does not)
    # WHEN reading a single item filtered on description == "shared", sorted
    # by role_id in the given orientation
    role = role_repo.read_single_item(
        where("description", "eq", "shared"),
        sort_by=order("role_id", orientation),
    )

    # THEN the first row per that ordering is the one returned: "a" when
    # ascending, "b" when descending
    assert role is not None
    assert role.role_id == f"{PREFIX}-{expected}"


def test_read_single_item_with_joins(db_session, roles):
    # GIVEN a user whose only role is roles[1] ("c")
    user = UserFactory.build()
    db_session.add(UserRoleFactory.build(user=user, role=roles[1]))
    db_session.flush()
    user_repo = CRUDRepository(db_session, User)

    # WHEN reading a single User, filtering through the joined roles
    # relationship on roles.role_id
    found = user_repo.read_single_item(
        where("roles.role_id", "eq", roles[1].role_id), joins=[User.roles]
    )

    # THEN the join correctly resolves back to that user
    assert found is user


# MARK: read_by_pk
def test_read_by_pk_returns_item(role_repo, roles):
    # GIVEN roles a, b, c (roles[2] is role "a")
    # WHEN reading by primary key "a"
    # THEN the matching instance is returned
    assert role_repo.read_by_pk(f"{PREFIX}-a") is roles[2]


def test_read_by_pk_returns_none_when_missing(role_repo):
    # GIVEN no role with this id exists
    # WHEN reading by that primary key
    # THEN None is returned rather than raising
    assert role_repo.read_by_pk(f"{PREFIX}-missing") is None


def test_read_by_pk_with_composite_key(db_session, role_permissions):
    # GIVEN a RolePermission, whose primary key is the composite
    # (role_id, permission_id)
    repo = CRUDRepository(db_session, RolePermission)
    rp = role_permissions[0]

    # WHEN reading by that composite key as a tuple
    # THEN the matching instance is returned
    assert repo.read_by_pk((rp.role_id, rp.permission_id)) is rp


# MARK: read_multiple_items
@pytest.mark.usefixtures("roles")
def test_read_multiple_items_with_filters_and_sort(role_repo):
    # GIVEN roles a, b, c
    # WHEN reading multiple items filtered to this test's prefix, sorted by
    # role_id descending
    result = role_repo.read_multiple_items(
        filters=PREFIXED, sort_by=order("role_id", "desc")
    )

    # THEN rows come back in that exact descending order
    assert [r.role_id for r in result] == [
        f"{PREFIX}-c",
        f"{PREFIX}-b",
        f"{PREFIX}-a",
    ]


def test_read_multiple_items_without_sort(role_repo, roles):
    # GIVEN roles a, b, c
    # WHEN reading multiple items with a filter but no sort_by
    result = role_repo.read_multiple_items(filters=PREFIXED)

    # THEN every matching row is returned, order unspecified (so compared
    # as sorted sets rather than asserting a particular sequence)
    assert sorted(r.role_id for r in result) == sorted(r.role_id for r in roles)


def test_read_multiple_items_without_filters_returns_everything(
    db_session, role_repo, roles
):
    # GIVEN roles a, b, c alongside whatever else is already seeded
    # WHEN reading multiple items with no filters at all
    result = role_repo.read_multiple_items()

    # THEN every row in the table is returned, including this test's roles
    all_role_ids = set(db_session.scalars(select(Role.role_id)))
    assert {r.role_id for r in result} == all_role_ids
    assert {r.role_id for r in roles} <= all_role_ids


def test_read_multiple_items_with_joins(db_session, roles):
    # GIVEN two users with roles[0] ("b") and one user with roles[1] ("c")
    users = [UserFactory.build() for _ in range(2)]
    for user in users:
        db_session.add(UserRoleFactory.build(user=user, role=roles[0]))
    db_session.add(UserRoleFactory.build(user=UserFactory.build(), role=roles[1]))
    db_session.flush()
    user_repo = CRUDRepository(db_session, User)

    # WHEN reading multiple Users, filtering through the joined roles
    # relationship on roles[0]'s role_id
    result = user_repo.read_multiple_items(
        filters=where("roles.role_id", "eq", roles[0].role_id),
        joins=[User.roles],
    )

    # THEN only the two users linked to roles[0] are returned
    assert {u.user_id for u in result} == {u.user_id for u in users}


# MARK: read_paginated_items
def test_read_paginated_items_requires_sort_by(role_repo):
    # GIVEN pagination is inherently order-dependent (LIMIT/OFFSET needs a
    # deterministic ORDER BY, otherwise pages can repeat/skip rows)
    # WHEN sort_by is explicitly empty
    # THEN the repository refuses up front rather than returning
    # non-deterministic pages
    with pytest.raises(NoOrderByColumnsSpecified):
        role_repo.read_paginated_items(sort_by=[], filters=PREFIXED)


@pytest.mark.usefixtures("roles")
def test_read_paginated_items_returns_requested_page(role_repo):
    # GIVEN roles a, b, c and a page size of 2
    # WHEN requesting page 1, then page 2, sorted by role_id ascending
    with set_params(Params(page=1, size=2)):
        first = role_repo.read_paginated_items(
            sort_by=order("role_id"), filters=PREFIXED
        )
    with set_params(Params(page=2, size=2)):
        second = role_repo.read_paginated_items(
            sort_by=order("role_id"), filters=PREFIXED
        )

    # THEN the total reflects all 3 rows, page 1 holds a & b, page 2 holds c
    assert first.total == 3
    assert [r.role_id for r in first.items] == [f"{PREFIX}-a", f"{PREFIX}-b"]
    assert [r.role_id for r in second.items] == [f"{PREFIX}-c"]


def test_read_paginated_items_with_joins(db_session, roles):
    # GIVEN three users with roles[0] ("b") and one user with roles[1] ("c")
    users = [UserFactory.build() for _ in range(3)]
    for user in users:
        db_session.add(UserRoleFactory.build(user=user, role=roles[0]))
    db_session.add(UserRoleFactory.build(user=UserFactory.build(), role=roles[1]))
    db_session.flush()
    user_repo = CRUDRepository(db_session, User)

    # WHEN requesting page 1 (size 2) of Users filtered through the joined
    # roles relationship on roles[0], sorted by email
    with set_params(Params(page=1, size=2)):
        page = user_repo.read_paginated_items(
            sort_by=order("email"),
            filters=where("roles.role_id", "eq", roles[0].role_id),
            joins=[User.roles],
        )

    # THEN the total reflects all 3 matching users, and the page holds the
    # first 2 of them by email order
    assert page.total == 3
    assert [u.email for u in page.items] == sorted(u.email for u in users)[:2]


# MARK: update_multiple_items_with_same_values
@pytest.mark.usefixtures("roles")
def test_update_same_values_updates_matching_rows(db_session, role_repo):
    # GIVEN roles a and b share description "shared"; role c is "unique"
    # WHEN updating every row matching description == "shared" to the same
    # new value ("changed")
    updated = role_repo.update_multiple_items_with_same_values(
        where("description", "eq", "shared"), {"description": "changed"}
    )

    # THEN the two matching rows are returned and persisted with the new
    # value; role c, which didn't match the filter, is untouched
    assert sorted(r.role_id for r in updated) == [f"{PREFIX}-a", f"{PREFIX}-b"]
    assert {r.role_id: r.description for r in get_roles(db_session)} == {
        f"{PREFIX}-a": "changed",
        f"{PREFIX}-b": "changed",
        f"{PREFIX}-c": "unique",
    }


@pytest.mark.usefixtures("roles")
def test_update_same_values_returns_empty_when_no_match(role_repo):
    # GIVEN roles a, b, c
    # WHEN updating with a filter that matches nothing
    updated = role_repo.update_multiple_items_with_same_values(
        where("role_id", "eq", f"{PREFIX}-nope"), {"description": "changed"}
    )

    # THEN an empty list is returned -- no rows touched
    assert updated == []


@pytest.mark.usefixtures("roles")
def test_update_same_values_without_commit_is_rolled_back(db_session, role_repo):
    # GIVEN an open savepoint over roles a, b, c
    savepoint = db_session.begin_nested()
    # WHEN updating all prefixed rows with commit=False
    updated = role_repo.update_multiple_items_with_same_values(
        PREFIXED, {"description": "changed"}, commit=False
    )
    assert len(updated) == 3

    # THEN rolling back the savepoint restores the original descriptions --
    # the update was never durable
    savepoint.rollback()
    assert [r.description for r in get_roles(db_session)] == [
        "shared",
        "shared",
        "unique",
    ]


def test_update_same_values_with_joins_single_pk(db_session, roles):
    # GIVEN two users, each linked to a different role (roles[0] and
    # roles[1]), both starting with given_name "before"
    user = UserFactory.build(given_name="before")
    other = UserFactory.build(given_name="before")
    db_session.add(UserRoleFactory.build(user=user, role=roles[0]))
    db_session.add(UserRoleFactory.build(user=other, role=roles[1]))
    db_session.flush()
    user_repo = CRUDRepository(db_session, User)

    # WHEN updating Users joined through roles, filtered to roles[0]
    updated = user_repo.update_multiple_items_with_same_values(
        where("roles.role_id", "eq", roles[0].role_id),
        {"given_name": "after"},
        joins=[User.roles],
    )

    # THEN only the user linked to roles[0] is updated; the other, linked
    # to a different role, is unaffected
    assert [u.user_id for u in updated] == [user.user_id]
    db_session.expire_all()
    assert user.given_name == "after"
    assert other.given_name == "before"


@pytest.mark.usefixtures("role_permissions")
def test_update_same_values_with_joins_composite_pk(db_session):
    # GIVEN role "rp-keep" has 2 RolePermissions and "rp-drop" has 1 --
    # RolePermission's primary key is the composite (role_id, permission_id)
    repo = CRUDRepository(db_session, RolePermission)
    keep_id = f"{PREFIX}-rp-keep"

    # WHEN updating RolePermissions joined through role, filtered to
    # "rp-keep"
    updated = repo.update_multiple_items_with_same_values(
        where("role.role_id", "eq", keep_id),
        {"created_by": None, "modified_by": None},
        joins=[RolePermission.role],
    )

    # THEN only the 2 rows belonging to "rp-keep" are updated, proving the
    # join-based filter resolves correctly even with a composite PK
    assert len(updated) == 2
    assert {rp.role_id for rp in updated} == {keep_id}


# MARK: update_multiple_items_with_different_values
@pytest.mark.usefixtures("roles")
def test_update_different_values_updates_each_row(db_session, role_repo):
    # GIVEN roles a, b, c
    # WHEN updating with no filter and a distinct payload per row (a gets
    # "first", b gets "second")
    role_repo.update_multiple_items_with_different_values(
        None,
        [
            {"role_id": f"{PREFIX}-a", "description": "first"},
            {"role_id": f"{PREFIX}-b", "description": "second"},
        ],
    )

    # THEN each row receives its own distinct value; role c, absent from
    # the payload, is untouched
    assert [r.description for r in get_roles(db_session)] == [
        "first",
        "second",
        "unique",
    ]


@pytest.mark.usefixtures("roles")
def test_update_different_values_respects_filters(db_session, role_repo):
    # GIVEN roles a, b, c, where only c has description "unique"
    # WHEN updating with a filter (description == "unique") and payloads for
    # both a and c
    role_repo.update_multiple_items_with_different_values(
        where("description", "eq", "unique"),
        [
            {"role_id": f"{PREFIX}-a", "description": "first"},
            {"role_id": f"{PREFIX}-c", "description": "third"},
        ],
    )

    # THEN role a is excluded by the filter even though it's in the payload
    # list, so only role c (which matches the filter) actually changes
    assert [r.description for r in get_roles(db_session)] == [
        "shared",
        "shared",
        "third",
    ]


@pytest.mark.usefixtures("roles")
def test_update_different_values_without_commit_is_rolled_back(db_session, role_repo):
    # GIVEN an open savepoint over roles a, b, c
    savepoint = db_session.begin_nested()
    # WHEN updating role a with commit=False
    role_repo.update_multiple_items_with_different_values(
        None, [{"role_id": f"{PREFIX}-a", "description": "first"}], commit=False
    )
    assert get_roles(db_session)[0].description == "first"

    # THEN rolling back the savepoint restores the original value
    savepoint.rollback()
    assert get_roles(db_session)[0].description == "shared"


# MARK: delete_multiple_items
@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_deletes_matching_rows(db_session, role_repo):
    # GIVEN roles a and b share description "shared"; role c is "unique"
    # WHEN deleting every row matching description == "shared"
    deleted = role_repo.delete_multiple_items(where("description", "eq", "shared"))

    # THEN the 2 matching rows are reported deleted, and only role c remains
    assert len(deleted) == 2
    assert [r.role_id for r in get_roles(db_session)] == [f"{PREFIX}-c"]


@pytest.mark.xfail(
    raises=ObjectDeletedError,
    strict=True,
    reason="commit expires the returned rows, which no longer exist to be reloaded",
)
@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_returned_rows_are_readable_after_commit(role_repo):
    # GIVEN roles a and b share description "shared"
    # WHEN deleting them with the default commit=True
    deleted = role_repo.delete_multiple_items(where("description", "eq", "shared"))

    # THEN (in principle) the returned rows' attributes should still be
    # readable -- but in practice they are NOT: `delete_multiple_items`
    # commits the session, and a plain `Session` defaults to
    # `expire_on_commit=True`, which expires every attribute on the
    # returned ORM objects. The *next* attribute access (`r.role_id` below)
    # tries to re-SELECT the row to refresh it, finds nothing because the
    # row was just deleted, and raises `ObjectDeletedError` instead of
    # yielding the value. This is a known, documented limitation -- `xfail`
    # with `strict=True` means the suite stays green today, but will fail
    # loudly (forcing the marker's removal) the moment someone fixes it.
    assert sorted(r.role_id for r in deleted) == [f"{PREFIX}-a", f"{PREFIX}-b"]


@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_returned_rows_are_readable_without_commit(role_repo):
    # GIVEN roles a and b share description "shared"
    # WHEN deleting them with commit=False (caller owns the transaction, so
    # nothing expires the returned objects' attributes)
    deleted = role_repo.delete_multiple_items(
        where("description", "eq", "shared"), commit=False
    )

    # THEN the returned rows' attributes are readable without error --
    # confirming the bug above is specifically about commit-triggered
    # expiration, not about DELETE ... RETURNING itself
    assert sorted(r.role_id for r in deleted) == [f"{PREFIX}-a", f"{PREFIX}-b"]


@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_returns_empty_when_no_match(db_session, role_repo):
    # GIVEN roles a, b, c
    # WHEN deleting with a filter that matches nothing
    deleted = role_repo.delete_multiple_items(where("role_id", "eq", f"{PREFIX}-x"))

    # THEN an empty list is returned and all 3 rows remain
    assert deleted == []
    assert len(get_roles(db_session)) == 3


@pytest.mark.usefixtures("roles")
def test_delete_multiple_items_without_commit_is_rolled_back(db_session, role_repo):
    # GIVEN an open savepoint over roles a, b, c
    savepoint = db_session.begin_nested()
    # WHEN deleting all prefixed rows with commit=False
    deleted = role_repo.delete_multiple_items(PREFIXED, commit=False)
    assert len(deleted) == 3

    # THEN rolling back the savepoint restores all 3 rows -- the delete was
    # never durable
    savepoint.rollback()
    assert len(get_roles(db_session)) == 3


def test_delete_multiple_items_with_joins_single_pk(db_session, roles):
    # GIVEN two users, each linked to a different role (roles[0] and
    # roles[1])
    user = UserFactory.build()
    other = UserFactory.build()
    db_session.add(UserRoleFactory.build(user=user, role=roles[0]))
    db_session.add(UserRoleFactory.build(user=other, role=roles[1]))
    db_session.flush()
    user_id, other_id = user.user_id, other.user_id
    user_repo = CRUDRepository(db_session, User)

    # WHEN deleting Users joined through roles, filtered to roles[0]
    deleted = user_repo.delete_multiple_items(
        where("roles.role_id", "eq", roles[0].role_id), joins=[User.roles]
    )

    # THEN only the user linked to roles[0] is deleted; the other, linked
    # to a different role, survives
    assert len(deleted) == 1
    db_session.expire_all()
    assert db_session.get(User, user_id) is None
    assert db_session.get(User, other_id) is not None


@pytest.mark.usefixtures("role_permissions")
def test_delete_multiple_items_with_joins_composite_pk(db_session):
    # GIVEN role "rp-keep" has 2 RolePermissions and "rp-drop" has 1 --
    # RolePermission's primary key is the composite (role_id, permission_id)
    repo = CRUDRepository(db_session, RolePermission)
    drop_id = f"{PREFIX}-rp-drop"

    # WHEN deleting RolePermissions joined through role, filtered to
    # "rp-drop"
    deleted = repo.delete_multiple_items(
        where("role.role_id", "eq", drop_id), joins=[RolePermission.role]
    )

    # THEN only the 1 row belonging to "rp-drop" is deleted; both rows for
    # "rp-keep" remain, proving the join-based filter resolves correctly
    # even with a composite PK
    assert len(deleted) == 1
    db_session.expire_all()
    remaining = db_session.scalars(
        select(RolePermission.role_id).where(RolePermission.role_id.like(f"{PREFIX}-%"))
    ).all()
    assert remaining == [f"{PREFIX}-rp-keep", f"{PREFIX}-rp-keep"]
