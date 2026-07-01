def test_list_certificate_requests_returns_first_page(
    client, cert_requests_url
):
    response = client.get(cert_requests_url)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 20
    assert "_links" in body
    assert "next" in body["_links"]


def test_certificate_request_summary_contains_expected_fields(
    client, cert_requests_url
):
    response = client.get(cert_requests_url)
    request = response.json()["items"][0]
    assert {
        "id",
        "nameAttributes",
        "createdWhen",
        "status",
    }.issubset(request)
    assert "userId" not in request
    assert "publicKey" not in request
    assert "extensions" not in request


def test_get_certificate_request_returns_detail(client, cert_requests_url):
    response = client.get(cert_requests_url)
    request_id = response.json()["items"][0]["id"]
    response = client.get(f"{cert_requests_url}/{request_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == request_id
    assert "userId" in body


def test_get_unknown_certificate_request_returns_404(
    client, cert_requests_url
):
    response = client.get(
        f"{cert_requests_url}/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Certificate request not found"
