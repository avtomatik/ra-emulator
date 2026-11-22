from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from app.main import create_app


def test_simulated_failure_is_configurable_and_health_still_works(settings):
    app = create_app(
        settings.model_copy(
            update={"failure_rate": 1.0, "failure_status": 529}
        )
    )
    client = TestClient(app)
    failure = client.get("/api/ra/certificates")
    assert failure.status_code == 529
    assert failure.json()["error"] == "SIMULATED_RA_FAILURE"
    assert client.get("/health").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_search_pagination_preserves_q_for_other_collections(client):
    for path in ("/api/ra/users", "/api/ra/certRequests"):
        response = client.get(path, params={"q": "а"})
        assert response.status_code == 200
        page = response.json()
        if "_links" in page:
            params = parse_qs(urlsplit(page["_links"]["next"]["href"]).query)
            assert params["q"] == ["а"]
