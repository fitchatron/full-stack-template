class NoOrderByColumnsSpecified(Exception):
    pass


class AppError(Exception):
    """
    Base domain error. Services raise these and the handler registered in
    app.api.exception_handlers turns them into a response with status_code.
    """

    status_code = 500
    code = "internal_error"
    headers: dict[str, str] | None = None

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    headers = {"WWW-Authenticate": "Bearer"}


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class UnprocessableContentError(AppError):
    status_code = 422
    code = "unprocessable_content"
