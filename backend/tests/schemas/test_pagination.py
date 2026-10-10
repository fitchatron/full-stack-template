import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_pagination import add_pagination, paginate

from app.schemas.base import BaseSchemaModel
from app.schemas.pagination import OptionalPage


class _ItemSchema(BaseSchemaModel):
    """Stand-in for any schema a paginated endpoint returns"""

    item_id: int


class _ItemSchemaPaginated(OptionalPage[_ItemSchema]):
    pass


_ITEMS = [_ItemSchema(item_id=item_id) for item_id in range(1, 6)]


@pytest.fixture(scope="module")
def pagination_client():
    """
    WHEN a FastAPI test client is created for a throwaway app with a paginated endpoint,
    THEN the client should be able to make requests to the endpoint and receive paginated responses.
    EXPECT the client to correctly handle the pagination logic without requiring a full application setup.
    """
    app = FastAPI()

    @app.get("/items")
    async def read_items() -> _ItemSchemaPaginated:
        return paginate(_ITEMS)

    add_pagination(app)

    return TestClient(app)


@pytest.mark.filterwarnings("ignore::fastapi_pagination.utils.FastAPIPaginationWarning")
@pytest.mark.parametrize(
    "params, expected_item_ids, expected_page, expected_size, expected_pages",
    [
        pytest.param(
            {},
            [1, 2, 3, 4, 5],
            1,
            5,
            1,
            id="no_params_returns_every_row_as_a_single_page",
        ),
        pytest.param(
            {"page": 2, "size": 2},
            [3, 4],
            2,
            2,
            3,
            id="page_and_size_returns_that_slice",
        ),
        pytest.param(
            {"size": 2},
            [1, 2],
            1,
            2,
            3,
            id="size_without_page_returns_the_first_page",
        ),
        pytest.param(
            {"page": 9, "size": 2},
            [],
            9,
            2,
            3,
            id="page_past_the_last_returns_no_rows",
        ),
    ],
)
def test_optional_page_returns_requested_rows(
    pagination_client,
    params,
    expected_item_ids,
    expected_page,
    expected_size,
    expected_pages,
):
    """
    WHEN a request is made to the paginated endpoint with specific query parameters,
    THEN the response should contain the expected subset of items along with correct pagination metadata.
    EXPECT the response to match the requested page, size, and total number of pages.
    """
    response = pagination_client.get("/items", params=params)

    assert response.status_code == 200

    body = response.json()
    assert [item["itemId"] for item in body["items"]] == expected_item_ids
    assert body["total"] == len(_ITEMS)
    assert (body["page"], body["size"], body["pages"]) == (
        expected_page,
        expected_size,
        expected_pages,
    )


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({"page": 0}, id="page_below_one"),
        pytest.param({"size": 0}, id="size_below_one"),
        pytest.param({"size": 101}, id="size_above_the_maximum"),
    ],
)
def test_optional_page_with_out_of_range_params_returns_422(pagination_client, params):
    """
    WHEN a request is made to the paginated endpoint with out-of-range query parameters,
    THEN the response should have a 422 Unprocessable Entity status code.
    EXPECT the server to reject requests with invalid pagination parameters.
    """
    response = pagination_client.get("/items", params=params)

    assert response.status_code == 422
