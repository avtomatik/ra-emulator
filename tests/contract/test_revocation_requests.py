from uuid import UUID

from app.domain.models.certificate import Certificate
from app.domain.models.revocation_request import RevocationRequest
from app.storage.sqlite import SQLiteStore


def test_revocation_list_has_real_records(client, rev_requests_url):
    response = client.get(rev_requests_url)
    assert response.status_code == 200
    requests = response.json()["items"]
    assert requests
    assert len(requests) == 20
    assert "_links" in response.json()
    assert {"revRequestId", "serialNumber", "thumbprint", "status"}.issubset(
        requests[0]
    )
    assert all(item["status"] == "Completed" for item in requests)
    assert all(item["serialNumber"] != "to-do" for item in requests)


def test_revocation_detail_links_to_revoked_certificate(
    client, rev_requests_url, certificates_url
):
    request = client.get(rev_requests_url).json()["items"][0]
    request_id = request["revRequestId"]
    UUID(request_id)
    detail = client.get(f"{rev_requests_url}/{request_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["revRequestId"] == request_id
    assert body["revocationReason"] == "KeyCompromise"
    assert body["folder"] == "default"
    certificate = client.get(f'{certificates_url}/{body["certificateId"]}')
    assert certificate.status_code == 200
    certificate_data = certificate.json()
    assert certificate_data["status"] == "Revoked"
    assert certificate_data["serialNumber"] == body["serialNumber"]
    assert certificate_data["thumbprint"] == body["thumbprint"]
    assert certificate_data["revokedWhen"] == body["resolvedWhen"]


def test_revocation_filter_by_serial_folder_and_unknown_id(
    client, rev_requests_url
):
    request = client.get(rev_requests_url).json()["items"][0]
    for query in (
        request["serialNumber"],
        request["thumbprint"],
        request["revRequestId"],
    ):
        response = client.get(
            rev_requests_url, params={"q": query, "folder": "default"}
        )
        assert response.status_code == 200
        assert request["revRequestId"] in [
            item["revRequestId"] for item in response.json()["items"]
        ]
    assert (
        client.get(rev_requests_url, params={"folder": "missing"}).json()[
            "items"
        ]
        == []
    )
    assert (
        client.get(
            f"{rev_requests_url}/00000000-0000-0000-0000-000000000000"
        ).status_code
        == 404
    )
    assert client.get(f"{rev_requests_url}/bad-id").status_code == 422


def test_generated_revocations_are_linked_consistently(settings):
    store = SQLiteStore(settings.database_path)
    certificates_by_id = {
        cert.id: cert for cert in store.all("certificates", Certificate)
    }
    for request in store.all("rev_requests", RevocationRequest):
        cert = certificates_by_id[request.certificate_id]
        assert cert.status == "Revoked"
        assert cert.folder == request.folder
        assert cert.serial_number == request.serial_number
        assert cert.thumbprint == request.thumbprint
        assert cert.revocation_reason == request.revocation_reason


def test_old_revocation_placeholders_do_not_block_legacy_datasets(
    monkeypatch, tmp_path
):
    from app.dataset import loader
    from app.dataset.generate import build_dataset

    dataset = build_dataset(number=3)
    original = {
        "users": [
            item.model_dump(mode="json", exclude_none=True)
            for item in dataset.users
        ],
        "certificates": [
            item.model_dump(mode="json", exclude_none=True)
            for item in dataset.certificates
        ],
        "cert_requests": [
            item.model_dump(mode="json", exclude_none=True)
            for item in dataset.cert_requests
        ],
    }
    old_placeholder = {
        "revRequestId": "00000000-0000-0000-0000-000000000001",
        "createdWhen": "2025-01-01T00:00:00Z",
        "resolvedWhen": "2025-01-01T00:00:00Z",
        "authRepliedWhen": "2025-01-01T00:00:00Z",
        "serialNumber": "to-do",
        "thumbprint": "to-do",
        "status": "RevocationRequestStatus:TO_DO",
    }
    (tmp_path / "rev_requests.json").write_text("[]")
    monkeypatch.setattr(loader, "SEEDS_DIR", tmp_path)
    monkeypatch.setattr(
        loader,
        "load_json",
        lambda name: (
            [old_placeholder] if name == "rev_requests" else original[name]
        ),
    )
    result = loader.load_dataset(default_folder="default")
    assert len(result.certificates) == 3
    assert result.rev_requests == ()
