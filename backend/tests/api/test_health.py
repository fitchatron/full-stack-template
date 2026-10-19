import logging
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import OperationalError

from app.api.deps import get_db
from app.main import app

BASE_URL = "/health"


class BrokenSession:
    """
    Stands in for a session whose database is unreachable.
    """

    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT NOW();", {}, Exception("connection refused"))


@pytest.fixture
def client_db_down(client):
    """
    The test client, with get_db pointed at a session that fails. Replaces the
    client fixture's override; the client fixture removes it on teardown.
    """
    app.dependency_overrides[get_db] = lambda: BrokenSession()
    return client


def test_health_endpoint(client):
    """
    WHEN a request is made to the health endpoint,
    THEN the health endpoint should return the appropriate status code.
    EXPECT the response to reflect the status of the service.
    """

    # no redirects: Docker's curl healthcheck doesn't follow them
    response = client.get(BASE_URL, follow_redirects=False)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_endpoint_ignores_database(client_db_down):
    """
    WHEN the database is unreachable,
    THEN the health endpoint should still report the service as up.
    EXPECT a 200, since liveness doesn't depend on the database.
    """

    response = client_db_down.get(BASE_URL, follow_redirects=False)

    assert response.status_code == 200


def test_readiness_endpoint(client):
    """
    WHEN a request is made to the readiness endpoint,
    THEN the readiness endpoint should return the appropriate status code.
    EXPECT the response to reflect the readiness of the service.
    """

    response = client.get(f"{BASE_URL}/ready", follow_redirects=False)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"

    # NOW() is the transaction start, which the fixture opens before the request
    timestamp = datetime.fromisoformat(body["timestamp"])
    assert timestamp.tzinfo is not None
    assert abs(datetime.now(UTC) - timestamp) < timedelta(minutes=1)


def test_readiness_endpoint_database_down(client_db_down):
    """
    WHEN the database is unreachable,
    THEN the readiness endpoint should report the service as not ready.
    EXPECT a 503 so healthchecks and monitors see the failure.
    """

    response = client_db_down.get(f"{BASE_URL}/ready", follow_redirects=False)

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is not ready"


def test_health_endpoints_not_logged(client, caplog):
    """
    WHEN the health and readiness endpoints succeed,
    THEN the request middleware should skip the access log line.
    EXPECT no log records for either path.
    """

    with caplog.at_level(logging.INFO, logger="app.main"):
        client.get(BASE_URL)
        client.get(f"{BASE_URL}/ready")

    access_logs = [r for r in caplog.records if r.name == "app.main"]
    assert not [r for r in access_logs if BASE_URL in r.getMessage()]


def test_readiness_failure_logged(client_db_down, caplog):
    """
    WHEN the readiness endpoint fails,
    THEN the request middleware should still write the access log line.
    EXPECT a log record for the 503.
    """

    with caplog.at_level(logging.INFO, logger="app.main"):
        client_db_down.get(f"{BASE_URL}/ready")

    access_logs = [r for r in caplog.records if r.name == "app.main"]
    assert any(f"{BASE_URL}/ready -> 503" in r.getMessage() for r in access_logs)
