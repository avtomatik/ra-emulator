from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.dataset.models import Dataset
from app.domain.models.certificate import Certificate
from app.domain.models.certificate_request import CertificateRequest
from app.domain.models.revocation_request import RevocationRequest
from app.domain.models.user import User
from app.main import create_app
from app.storage.sqlite import SQLiteStore


def load_sqlite_dataset(store: SQLiteStore) -> Dataset:
    return Dataset(
        certificates=tuple(store.all("certificates", Certificate)),
        cert_requests=tuple(store.all("cert_requests", CertificateRequest)),
        rev_requests=tuple(store.all("rev_requests", RevocationRequest)),
        users=tuple(store.all("users", User)),
    )


def test_single_folder_matches_legacy_unfiltered_collection(
    client, certificates_url
):
    without_folder = client.get(certificates_url)
    with_folder = client.get(certificates_url, params={"folder": "default"})
    assert without_folder.status_code == with_folder.status_code == 200
    assert without_folder.json()["items"] == with_folder.json()["items"]
    # Compare through every page, not only the first 20 records.
    unfiltered_ids, folder_ids = [], []
    for url, output in [
        (certificates_url, unfiltered_ids),
        (f"{certificates_url}?folder=default", folder_ids),
    ]:
        while url:
            page = client.get(url).json()
            output.extend(item["id"] for item in page["items"])
            url = page.get("_links", {}).get("next", {}).get("href")
    assert unfiltered_ids == folder_ids
    assert len(folder_ids) == 100


def test_multiple_folders_filter_and_retain_context_in_next_page(settings):
    store = SQLiteStore(settings.database_path)
    dataset = load_sqlite_dataset(store)
    certificates = tuple(
        c.model_copy(
            update={"folder": "production folder/2026" if i % 2 else "archive"}
        )
        for i, c in enumerate(dataset.certificates)
    )
    # Keep revocation links consistent with their certificates.
    folder_by_id = {cert.id: cert.folder for cert in certificates}
    rev_requests = tuple(
        r.model_copy(update={"folder": folder_by_id[r.certificate_id]})
        for r in dataset.rev_requests
    )
    store.replace_dataset(
        Dataset(
            certificates=certificates,
            cert_requests=dataset.cert_requests,
            rev_requests=rev_requests,
            users=dataset.users,
        )
    )
    client = TestClient(
        create_app(
            settings.model_copy(
                update={
                    "certificate_folders": (
                        "archive",
                        "production folder/2026",
                    )
                }
            )
        )
    )

    def collect(path):
        ids = []
        pages = []
        while path:
            response = client.get(path)
            assert response.status_code == 200
            page = response.json()
            ids.extend(item["id"] for item in page["items"])
            pages.append(page)
            path = page.get("_links", {}).get("next", {}).get("href")
        return ids, pages

    all_ids, _ = collect("/api/ra/certificates")
    archive_ids, archive_pages = collect("/api/ra/certificates?folder=archive")
    production_ids, production_pages = collect(
        "/api/ra/certificates?folder=production%20folder%2F2026"
    )
    assert len(all_ids) == 100
    assert len(archive_ids) == len(production_ids) == 50
    assert set(archive_ids).isdisjoint(production_ids)
    assert set(all_ids) == set(archive_ids) | set(production_ids)
    assert parse_qs(
        urlsplit(archive_pages[0]["_links"]["next"]["href"]).query
    )["folder"] == ["archive"]
    assert parse_qs(
        urlsplit(production_pages[0]["_links"]["next"]["href"]).query
    )["folder"] == ["production folder/2026"]
    assert (
        client.get("/api/ra/certificates?folder=missing").json()["items"] == []
    )
    detail = client.get(f"/api/ra/certificates/{production_ids[0]}").json()
    assert detail["folder"] == "production folder/2026"


def test_search_pagination_preserves_folder_and_query(settings):
    client = TestClient(create_app(settings))
    # Every serial in the seeded dataset is hexadecimal, and '0' occurs in many.
    response = client.get(
        "/api/ra/certificates", params={"q": "0", "folder": "default"}
    )
    assert response.status_code == 200
    assert response.json().get("_links")
    next_href = response.json()["_links"]["next"]["href"]
    params = parse_qs(urlsplit(next_href).query)
    assert params["q"] == ["0"]
    assert params["folder"] == ["default"]
    subsequent = client.get(next_href).json()["items"]
    assert all(
        "0" in certificate["serialNumber"].lower()
        or "0" in certificate["thumbprint"].lower()
        or "0" in certificate["nameAttributes"]["commonName"].lower()
        for certificate in subsequent
    )


def test_folders_reject_empty_entries_and_deduplicate():
    import pytest

    assert Settings(
        certificate_folders="default, archive,default"
    ).certificate_folders == ("default", "archive")
    for value in ("", ",default", "default,,archive"):
        with pytest.raises(ValueError):
            Settings(certificate_folders=value)


def test_search_value_parameter_used_by_radp_client(client, certificates_url):
    items = client.get(certificates_url).json()["items"]
    serial = items[0]["serialNumber"]
    response = client.get(
        certificates_url, params={"value": serial, "folder": "default"}
    )
    assert response.status_code == 200
    assert any(
        item["serialNumber"] == serial for item in response.json()["items"]
    )


def test_value_search_kept_in_page_link(client, certificates_url):
    first_page = client.get(
        certificates_url, params={"value": "0", "folder": "default"}
    ).json()
    assert "_links" in first_page
    parameters = parse_qs(urlsplit(first_page["_links"]["next"]["href"]).query)
    assert parameters["folder"] == ["default"]
    assert parameters["value"] == ["0"]
