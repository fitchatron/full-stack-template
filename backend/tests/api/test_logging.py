import asyncio
import logging
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError
from starlette.requests import Request

from app.api.exception_handlers import integrity_error_handler
from app.core.config import settings
from app.core.logging import RequestIdFilter, request_id_ctx
from app.main import app

LOGIN_URL = "/api/v1/auth/login"
BOOM_PATH = "/__test__/boom"


@pytest.fixture
def logs(caplog):
    """
    caplog with the request id filter attached, so records carry request_id the
    same way they do through the real handler
    """
    request_id_filter = RequestIdFilter()
    caplog.handler.addFilter(request_id_filter)
    caplog.set_level(logging.INFO)
    yield caplog
    caplog.handler.removeFilter(request_id_filter)


@pytest.fixture
def boom_route():
    """
    Temporarily add a route that raises an unhandled exception
    """

    def boom():
        raise RuntimeError("kaboom")

    app.add_api_route(BOOM_PATH, boom, methods=["GET"])
    route = app.router.routes[-1]
    yield
    app.router.routes.remove(route)


def records_from(caplog, logger_name: str) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == logger_name]


def make_request(method: str = "POST", path: str = "/api/v1/things") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "query_string": b"",
            "headers": [],
        }
    )


def make_integrity_error(constraint_name: str | None) -> IntegrityError:
    orig = Exception("constraint violated")
    orig.diag = SimpleNamespace(constraint_name=constraint_name)
    return IntegrityError("INSERT ...", {}, orig)


# MARK: request context middleware
def test_access_log_line(client, logs):
    """
    WHEN a request is handled,
    THEN the middleware should write one access log line.
    EXPECT the method, path, status and duration in the message.
    """
    response = client.post(LOGIN_URL, data={"username": "x@y.z", "password": "p"})

    (record,) = records_from(logs, "app.main")
    assert record.levelno == logging.INFO
    assert record.getMessage().startswith(f"POST {LOGIN_URL} -> 400 (")
    assert record.getMessage().endswith("ms)")
    assert record.request_id == response.headers["X-Request-ID"]


@pytest.mark.parametrize(
    "inbound_id, is_trusted",
    [
        pytest.param("trace-abc-123", True, id="valid"),
        pytest.param("a" * 64, True, id="max-length"),
        pytest.param("a" * 65, False, id="too-long"),
        pytest.param("bad id with spaces", False, id="invalid-chars"),
        pytest.param("", False, id="empty"),
    ],
)
def test_inbound_request_id(client, logs, inbound_id, is_trusted):
    """
    WHEN a request arrives with an X-Request-ID header,
    THEN the middleware should reuse it only if it is safe to log.
    EXPECT safe ids to be echoed and unsafe ones replaced with a fresh hex id.
    """
    response = client.post(
        LOGIN_URL,
        data={"username": "x@y.z", "password": "p"},
        headers={"X-Request-ID": inbound_id},
    )

    request_id = response.headers["X-Request-ID"]
    if is_trusted:
        assert request_id == inbound_id
    else:
        assert request_id != inbound_id
        assert len(request_id) == 32
        int(request_id, 16)

    # every app record logged during the request carries the same id
    app_records = [r for r in logs.records if r.name.startswith("app.")]
    assert app_records
    assert {r.request_id for r in app_records} == {request_id}


def test_request_id_reset_after_request(client):
    """
    WHEN a request has finished,
    THEN the request id context should be cleared.
    EXPECT logs outside a request to fall back to "-".
    """
    client.post(LOGIN_URL, data={"username": "x@y.z", "password": "p"})

    assert request_id_ctx.get() == "-"


@pytest.mark.usefixtures("boom_route")
def test_unhandled_exception_is_logged(client, logs):
    """
    WHEN a route raises an unhandled exception,
    THEN the middleware should log it with a traceback and return a 500.
    EXPECT a generic body that does not leak the exception message.
    """
    response = client.get(BOOM_PATH)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "X-Request-ID" in response.headers

    error, access = records_from(logs, "app.main")
    assert error.levelno == logging.ERROR
    assert error.getMessage() == f"Unhandled error on GET {BOOM_PATH}"
    assert isinstance(error.exc_info[1], RuntimeError)
    assert access.getMessage().startswith(f"GET {BOOM_PATH} -> 500 (")


# MARK: exception handlers
def test_app_error_logged_without_traceback(client, logs):
    """
    WHEN a service raises a domain error,
    THEN the handler should log the reason at INFO.
    EXPECT no traceback, since domain errors are expected outcomes.
    """
    client.post(LOGIN_URL, data={"username": "x@y.z", "password": "p"})

    (record,) = records_from(logs, "app.api.exception_handlers")
    assert record.levelno == logging.INFO
    assert record.exc_info is None
    assert record.getMessage() == (
        f"POST {LOGIN_URL} -> 400: Incorrect email or password"
    )


def test_integrity_error_unique_constraint(logs):
    """
    WHEN a unique constraint is violated,
    THEN the handler should log the constraint at INFO and return a 409.
    EXPECT no traceback.
    """
    response = asyncio.run(
        integrity_error_handler(
            make_request(), make_integrity_error("uq__users__email")
        )
    )

    assert response.status_code == 409
    (record,) = records_from(logs, "app.api.exception_handlers")
    assert record.levelno == logging.INFO
    assert record.exc_info is None
    assert "uq__users__email" in record.getMessage()


@pytest.mark.parametrize(
    "constraint_name",
    [
        pytest.param("fk__users__role_id", id="other-constraint"),
        pytest.param(None, id="no-constraint"),
    ],
)
def test_integrity_error_other(logs, constraint_name):
    """
    WHEN any other integrity error occurs,
    THEN the handler should log it with a traceback and return a 500.
    EXPECT the log to be at ERROR level.
    """
    response = asyncio.run(
        integrity_error_handler(make_request(), make_integrity_error(constraint_name))
    )

    assert response.status_code == 500
    (record,) = records_from(logs, "app.api.exception_handlers")
    assert record.levelno == logging.ERROR
    assert record.exc_info is not None
    assert record.getMessage() == "Integrity error on POST /api/v1/things"


# MARK: auth service
@pytest.mark.parametrize(
    "case, expected_message",
    [
        pytest.param(
            "unknown-email",
            "Authentication failed for non-existent user with email: {email}",
            id="unknown-email",
        ),
        pytest.param(
            "wrong-password",
            "Authentication failed for user with email: {email} due to incorrect password",
            id="wrong-password",
        ),
        pytest.param(
            "inactive",
            "Inactive user attempted to authenticate: {user_id}",
            id="inactive",
        ),
    ],
)
def test_failed_login_is_logged(
    client, db_session, act_as_user, logs, case, expected_message
):
    """
    WHEN a login attempt fails,
    THEN the auth service should log a warning with the reason.
    EXPECT exactly one warning from app.services.auth.
    """
    email = act_as_user.email
    password = settings.TEST_USER_PASSWORD
    if case == "unknown-email":
        email = "nobody@test.example.com"
    elif case == "wrong-password":
        password = "wrong-password"
    elif case == "inactive":
        act_as_user.is_active = False
        db_session.flush()

    client.post(LOGIN_URL, data={"username": email, "password": password})

    (record,) = records_from(logs, "app.services.auth")
    assert record.levelno == logging.WARNING
    assert record.getMessage() == expected_message.format(
        email=email, user_id=act_as_user.user_id
    )


def test_successful_login_logs_no_warning(client, act_as_user, logs):
    """
    WHEN a login succeeds,
    THEN the auth service should not log anything.
    EXPECT no records from app.services.auth.
    """
    response = client.post(
        LOGIN_URL,
        data={"username": act_as_user.email, "password": settings.TEST_USER_PASSWORD},
    )

    assert response.status_code == 200
    assert records_from(logs, "app.services.auth") == []
