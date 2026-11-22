"""Contract, transaction and durability checks for synthetic write operations."""

from concurrent.futures import ThreadPoolExecutor
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from app.domain.models.certificate import Certificate
from app.main import create_app
from app.storage.sqlite import SQLiteStore


def available_certificate(client):
    path = "/api/ra/certificates"
    while path:
        page = client.get(path).json()
        for item in page["items"]:
            if item["status"].casefold() == "valid":
                return client.get(f"/api/ra/certificates/{item['id']}").json()
        path = page.get("_links", {}).get("next", {}).get("href")
    raise AssertionError("No valid certificate in seed dataset")


def test_revocation_requests_use_the_same_paginated_contract(client):
    url = "/api/ra/revRequests?folder=default"
    seen = []
    pages = 0
    while url:
        response = client.get(url)
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) <= 20
        seen.extend(item["revRequestId"] for item in body["items"])
        pages += 1
        url = body.get("_links", {}).get("next", {}).get("href")
        if url:
            params = parse_qs(urlsplit(url).query)
            assert params["folder"] == ["default"]
            assert "pageToken" in params
    assert pages == 2
    assert len(seen) == len(set(seen)) == 34
    assert client.get("/api/ra/revRequests?folder=unknown").json() == {
        "items": []
    }


def test_revocation_pagination_keeps_search_query(client):
    response = client.get(
        "/api/ra/revRequests", params={"folder": "default", "value": "0"}
    )
    body = response.json()
    if "_links" in body:
        params = parse_qs(urlsplit(body["_links"]["next"]["href"]).query)
        assert params["folder"] == ["default"]
        assert params["value"] == ["0"]
    assert client.get("/api/ra/revRequests?pageToken=bad").status_code == 400


def test_create_approve_updates_certificate_and_survives_restart(
    client, settings
):
    certificate = available_certificate(client)
    cert_id = certificate["id"]
    response = client.post(
        "/api/ra/revRequests",
        json={"certificateId": cert_id, "revocationReason": "KeyCompromise"},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "Pending"
    assert created["folder"] == certificate["folder"]
    assert "resolvedWhen" not in created
    assert (
        client.post(
            "/api/ra/revRequests", json={"certificateId": cert_id}
        ).status_code
        == 409
    )
    assert (
        client.get(f"/api/ra/certificates/{cert_id}").json()["status"]
        == "VALID"
    )
    request_id = created["revRequestId"]
    approved = client.post(
        f"/api/ra/revRequests/{request_id}/approve", json={}
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "Completed"
    assert approved.json()["resolvedWhen"]
    assert (
        client.post(f"/api/ra/revRequests/{request_id}/approve").status_code
        == 409
    )
    assert (
        client.post(f"/api/ra/revRequests/{request_id}/reject").status_code
        == 409
    )
    assert (
        client.post(
            "/api/ra/revRequests", json={"certificateId": cert_id}
        ).status_code
        == 409
    )
    restarted = TestClient(create_app(settings))
    persisted = restarted.get(f"/api/ra/revRequests/{request_id}").json()
    cert = restarted.get(f"/api/ra/certificates/{cert_id}").json()
    assert persisted["status"] == "Completed"
    assert cert["status"] == "Revoked"
    assert persisted["resolvedWhen"] == cert["revokedWhen"]
    assert persisted["serialNumber"] == cert["serialNumber"]
    assert persisted["thumbprint"] == cert["thumbprint"]
    assert cert["revocationReason"] == "KeyCompromise"


def test_reject_leaves_certificate_valid_and_allows_new_request(client):
    certificate = available_certificate(client)
    cert_id = certificate["id"]
    response = client.post(
        "/api/ra/revRequests", json={"certificateId": cert_id}
    )
    assert response.status_code == 201
    request_id = response.json()["revRequestId"]
    rejected = client.post(f"/api/ra/revRequests/{request_id}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "Rejected"
    assert (
        client.get(f"/api/ra/certificates/{cert_id}").json()["status"]
        == "VALID"
    )
    repeated = client.post(
        "/api/ra/revRequests", json={"certificateId": cert_id}
    )
    assert repeated.status_code == 201
    assert repeated.json()["revRequestId"] != request_id
    assert (
        client.post(f"/api/ra/revRequests/{request_id}/approve").status_code
        == 409
    )


def test_missing_links_and_validation_errors(client):
    missing = "00000000-0000-0000-0000-000000000000"
    assert (
        client.post(
            "/api/ra/revRequests", json={"certificateId": missing}
        ).status_code
        == 404
    )
    assert (
        client.post(f"/api/ra/revRequests/{missing}/approve").status_code
        == 404
    )
    assert (
        client.post(f"/api/ra/revRequests/{missing}/reject").status_code == 404
    )
    assert (
        client.post(
            "/api/ra/revRequests", json={"certificateId": "bad-id"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/ra/revRequests",
            json={"certificateId": missing, "revocationReason": "random"},
        ).status_code
        == 422
    )


def test_invalid_certificate_state_does_not_commit_request(client):
    revoked = client.get("/api/ra/revRequests").json()["items"][0]
    cert_id = client.get(
        f"/api/ra/revRequests/{revoked['revRequestId']}"
    ).json()["certificateId"]
    before = len(client.get("/api/ra/revRequests").json()["items"])
    assert (
        client.post(
            "/api/ra/revRequests", json={"certificateId": cert_id}
        ).status_code
        == 409
    )
    after = len(client.get("/api/ra/revRequests").json()["items"])
    assert after == before


def test_atomic_failure_preserves_pending_request(client, settings):
    certificate = available_certificate(client)
    req_id = client.post(
        "/api/ra/revRequests", json={"certificateId": certificate["id"]}
    ).json()["revRequestId"]
    store = SQLiteStore(settings.database_path)
    with store.connection() as conn:
        cert = store.get(
            "certificates", certificate["id"], Certificate
        )  # id string accepted by sqlite
        cert.status = "Expired"
        store._put(conn, "certificates", cert, id_field="id")
    assert (
        client.post(f"/api/ra/revRequests/{req_id}/approve").status_code == 409
    )
    assert (
        client.get(f"/api/ra/revRequests/{req_id}").json()["status"]
        == "Pending"
    )
    assert (
        client.get(f"/api/ra/certificates/{certificate['id']}").json()[
            "status"
        ]
        == "Expired"
    )


def test_concurrent_creation_allows_one_request(client):
    certificate = available_certificate(client)
    payload = {"certificateId": certificate["id"]}
    with ThreadPoolExecutor(max_workers=2) as executor:
        result = list(
            executor.map(
                lambda _: client.post(
                    "/api/ra/revRequests", json=payload
                ).status_code,
                (1, 2),
            )
        )
    assert sorted(result) == [201, 409]
