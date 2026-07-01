from uuid import UUID


def test_list_certificates_returns_first_page(client, certificates_url):
    response = client.get(certificates_url)
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 20
    assert "_links" in body
    assert "next" in body["_links"]
    assert "href" in body["_links"]["next"]


def test_list_certificates_returns_expected_summary_fields(
    client, certificates_url
):
    response = client.get(certificates_url)
    assert response.status_code == 200
    certificate = response.json()["items"][0]
    assert {
        "id",
        "nameAttributes",
        "serialNumber",
        "thumbprint",
        "notBefore",
        "notAfter",
        "keyNotAfter",
        "createdWhen",
        "status",
    }.issubset(certificate)
    assert "certRequestId" not in certificate
    assert "rawCertificate" not in certificate
    UUID(certificate["id"])


def test_get_certificate_returns_detail(client, certificates_url):
    response = client.get(certificates_url)
    certificate_id = response.json()["items"][0]["id"]
    response = client.get(f"{certificates_url}/{certificate_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == certificate_id
    assert "serialNumber" in body
    assert "thumbprint" in body
    assert "rawCertificate" in body


def test_get_unknown_certificate_returns_404(client, certificates_url):
    response = client.get(
        f"{certificates_url}/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Certificate not found"


def test_get_certificate_with_invalid_uuid_returns_422(
    client, certificates_url
):
    response = client.get(f"{certificates_url}/not-a-uuid")
    assert response.status_code == 422


def test_certificate_query_filters_by_common_name(client, certificates_url):
    response = client.get(certificates_url)
    certificate = response.json()["items"][0]
    common_name = certificate["nameAttributes"]["commonName"]
    response = client.get(certificates_url, params={"q": common_name})
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(
        common_name.casefold()
        in item["nameAttributes"]["commonName"].casefold()
        for item in items
    )
