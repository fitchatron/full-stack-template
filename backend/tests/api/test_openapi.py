import pytest
from pydantic import TypeAdapter

from app.main import app
from app.schemas.api import HTTPExceptionSchema, HTTPValidationExceptionSchema

ERROR_SCHEMAS = {"HTTPExceptionSchema", "HTTPValidationExceptionSchema"}


def error_responses():
    """
    Every non-2xx response in the spec, as (operation, status code, schema name)
    """
    for path, operations in app.openapi()["paths"].items():
        for method, operation in operations.items():
            for status_code, response in operation["responses"].items():
                if status_code.startswith("2"):
                    continue
                schema = response["content"]["application/json"]["schema"]
                yield f"{method} {path}", status_code, schema["$ref"].split("/")[-1]


def test_error_responses_use_error_schemas():
    """
    WHEN the OpenAPI spec is generated,
    THEN every error response should reference the API's own error schemas.
    EXPECT no FastAPI defaults, which would generate wrong client types.
    """
    unexpected = [r for r in error_responses() if r[2] not in ERROR_SCHEMAS]

    assert unexpected == []


def test_spec_excludes_default_validation_schema():
    """
    WHEN the OpenAPI spec is generated,
    THEN FastAPI's default 422 schema should not be included.
    EXPECT generated clients to have no HTTPValidationError type.
    """
    assert "HTTPValidationError" not in app.openapi()["components"]["schemas"]


@pytest.mark.parametrize(
    "request_args, schema",
    [
        pytest.param(
            {
                "method": "POST",
                "url": "/api/v1/auth/register",
                "json": {"email": "not-an-email"},
            },
            HTTPValidationExceptionSchema,
            id="validation-error",
        ),
        pytest.param(
            {"method": "GET", "url": "/api/v1/does-not-exist"},
            HTTPExceptionSchema,
            id="http-error",
        ),
    ],
)
def test_error_body_matches_schema(client, request_args, schema):
    """
    WHEN a request fails,
    THEN the response body should match the schema published in the spec.
    EXPECT the body to validate without errors.
    """
    response = client.request(**request_args)

    assert response.status_code >= 400
    TypeAdapter(schema).validate_python(response.json())
