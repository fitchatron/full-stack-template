from pydantic import BaseModel, Field


class ErrorSchema(BaseModel):
    """
    Error returned by every failed request
    """

    code: str = Field(description="Stable machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: dict = Field(description="Extra context about the error")


class HTTPExceptionSchema(BaseModel):
    """
    Base HTTP exception schema
    """

    error: ErrorSchema


class ValidationIssueSchema(BaseModel):
    """
    A single field that failed request validation
    """

    loc: list[str | int] = Field(description="Path to the invalid value")
    msg: str = Field(description="Why the value is invalid")
    type: str = Field(description="Validation error type")


class ValidationDetailsSchema(BaseModel):
    """
    Request validation errors carry a list of issues. Other 422s, such as
    translated database errors, leave it out.
    """

    errors: list[ValidationIssueSchema] | None = None


class ValidationErrorSchema(ErrorSchema):
    """
    Error returned with a 422
    """

    details: ValidationDetailsSchema


class HTTPValidationExceptionSchema(BaseModel):
    """
    HTTP exception schema for a 422. Declared on routes in place of FastAPI's
    default HTTPValidationError, which describes a body this API doesn't return.
    """

    error: ValidationErrorSchema
