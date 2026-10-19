import re

BASE_URL = "/health"


def test_health_endpoint(client):
    """
    WHEN a request is made to the health endpoint,
    THEN the health endpoint should return the appropriate status code.
    EXPECT the response to reflect the status of the service.
    """

    response = client.get(
        f"{BASE_URL}",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_readiness_endpoint(client):
    """
    WHEN a request is made to the readiness endpoint,
    THEN the readiness endpoint should return the appropriate status code.
    EXPECT the response to reflect the readiness of the service.
    """

    response = client.get(
        f"{BASE_URL}/ready",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"

    assert "timestamp" in body
    assert body["timestamp"] is not None

    assert (
        re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}\+00:00",
            body["timestamp"],
        )
        is not None
    )
