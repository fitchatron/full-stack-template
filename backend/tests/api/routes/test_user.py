from pydantic import TypeAdapter
import pytest
from app.core.config import settings
from app.schemas.user import UserResponseSchema, UserResponseSchemaPaginated
from seeding.factories import UserFactory

BASE_URL = "/api/v1/users"


@pytest.mark.parametrize(
    "num_seed_users, page, size",
    [
        pytest.param(20, 1, 10, id="default"),
        pytest.param(20, 2, 5, id="second_page"),
    ],
)
def test_get_all_users(
    db_session, client, act_as_admin, auth_headers, num_seed_users, page, size
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

    validated_body = UserResponseSchemaPaginated.model_validate(body)

    assert len(validated_body.items) == size
    assert validated_body.total == num_seed_users + len([act_as_admin])
    assert validated_body.page == page
    assert validated_body.size == size


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
