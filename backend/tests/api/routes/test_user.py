from pydantic import TypeAdapter
import pytest
from app.core.config import settings
from app.schemas.user import UserResponseSchema
from seeding.factories import UserFactory

BASE_URL = "/api/v1/users"


@pytest.mark.parametrize(
    "num_seed_users, page, size, schema",
    [
        pytest.param(20, 1, 10, UserResponseSchema, id="default"),
        pytest.param(20, 2, 5, UserResponseSchema, id="second_page"),
    ],
)
def test_get_all_users(
    db_session, client, act_as_admin, auth_headers, num_seed_users, page, size, schema
):
    """
    Test that a valid user can retrieve all users.
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

    assert _is_paginated_response(body, schema)
    assert len(body["items"]) == size
    assert body["total"] == num_seed_users + len([act_as_admin])
    assert body["page"] == page
    assert body["size"] == size


# @pytest.mark.parametrize("", [])
# def test_get_user_by_id():
#     raise False


# @pytest.mark.parametrize("", [])
# def test_put_update_user_by_id():
#     raise False


# @pytest.mark.parametrize("", [])
# def test_patch_update_user_by_id():
#     raise False


# @pytest.mark.parametrize("", [])
# def test_delete_user_by_id():
#     raise False


def _is_paginated_response(data: dict, schema):
    return (
        isinstance(data, dict)
        and "items" in data
        and TypeAdapter(list[schema]).validate_python(data["items"])
        and "total" in data
        and isinstance(data["total"], int)
        and "page" in data
        and isinstance(data["page"], int)
        and "size" in data
        and isinstance(data["size"], int)
        and "links" in data
        and isinstance(data["links"], dict)
        and all(
            key in data["links"] for key in ["self", "first", "last", "next", "prev"]
        )
    )
