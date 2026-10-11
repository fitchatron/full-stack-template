import json
import logging
import sys

import pytest

from app.core import logging as app_logging
from app.core.logging import JsonFormatter, RequestIdFilter, request_id_ctx


def make_record(msg="hello %s", args=("world",), exc_info=None) -> logging.LogRecord:
    return logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=args,
        exc_info=exc_info,
    )


@pytest.fixture
def restore_logging():
    """
    setup_logging reconfigures the root logger, so put the app config back afterwards
    """
    yield
    app_logging.setup_logging()


def test_request_id_filter_defaults_outside_a_request():
    """
    WHEN a record is logged outside of a request,
    THEN the filter should tag it with the default request id.
    EXPECT request_id to be "-".
    """
    record = make_record()

    assert RequestIdFilter().filter(record) is True
    assert record.request_id == "-"


def test_request_id_filter_uses_current_request_id():
    """
    WHEN a record is logged while a request id is set,
    THEN the filter should copy it onto the record.
    EXPECT request_id to match the context value.
    """
    token = request_id_ctx.set("abc-123")
    try:
        record = make_record()
        RequestIdFilter().filter(record)
    finally:
        request_id_ctx.reset(token)

    assert record.request_id == "abc-123"


def test_json_formatter_outputs_one_json_object():
    """
    WHEN a record is formatted as JSON,
    THEN the output should be a single line of valid JSON.
    EXPECT the interpolated message and record metadata in the payload.
    """
    record = make_record()
    record.request_id = "abc-123"

    output = JsonFormatter().format(record)
    payload = json.loads(output)

    assert "\n" not in output
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["msg"] == "hello world"
    assert payload["request_id"] == "abc-123"
    assert payload["ts"].endswith("+00:00")
    assert "exc_info" not in payload


def test_json_formatter_includes_traceback():
    """
    WHEN a record carries exception info,
    THEN the formatter should include the traceback.
    EXPECT exc_info to name the exception and the output to stay on one line.
    """
    try:
        raise ValueError("boom")
    except ValueError:
        record = make_record(msg="failed", args=(), exc_info=sys.exc_info())

    output = JsonFormatter().format(record)
    payload = json.loads(output)

    assert "\n" not in output
    assert payload["request_id"] == "-"
    assert "ValueError: boom" in payload["exc_info"]


@pytest.mark.usefixtures("restore_logging")
@pytest.mark.parametrize(
    "fastapi_env, expected_formatter",
    [
        pytest.param("development", logging.Formatter, id="development-text"),
        pytest.param(None, JsonFormatter, id="other-json"),
    ],
)
def test_setup_logging_picks_formatter(monkeypatch, fastapi_env, expected_formatter):
    """
    WHEN logging is configured,
    THEN the root handler should use text in development and JSON elsewhere.
    EXPECT the formatter type to follow FASTAPI_ENV and noisy loggers to be tamed.
    """
    monkeypatch.setattr(app_logging.settings, "FASTAPI_ENV", fastapi_env)

    app_logging.setup_logging()

    root = logging.getLogger()
    assert len(root.handlers) == 1
    handler = root.handlers[0]
    assert type(handler.formatter) is expected_formatter
    assert any(isinstance(f, RequestIdFilter) for f in handler.filters)
    assert logging.getLogger("uvicorn.access").propagate is False
    assert logging.getLogger("sqlalchemy.engine").level == logging.WARNING
