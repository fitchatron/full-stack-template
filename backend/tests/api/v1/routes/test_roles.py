import pytest
from sqlalchemy import select

from app.models.model import Role
from app.schemas.role import RoleSchema, RoleSchemaPaginated
from seeding.factories import RoleFactory

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
def test_post_create_role():
    pass


# MARK: PUT tests
def test_put_update_role_by_id():
    pass


# MARK: PATCH tests
def test_patch_update_role_by_id():
    pass


# MARK: DELETE tests
def test_delete_role_by_id():
    pass
