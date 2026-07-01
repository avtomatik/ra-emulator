import base64


def test_missing_page_token_means_first_page(client, certificates_url):
    response = client.get(certificates_url)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 20


def test_invalid_page_token_returns_400(client, certificates_url):
    response = client.get(
        certificates_url, params={"pageToken": "definitely-invalid"}
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "INVALID_PAGE_TOKEN"
    assert body["message"] == "Invalid page token"


def test_negative_page_token_returns_400(client, certificates_url):
    token = base64.urlsafe_b64encode(b"-1").decode()
    response = client.get(certificates_url, params={"pageToken": token})
    assert response.status_code == 400


def test_non_numeric_page_token_returns_400(client, certificates_url):
    token = base64.urlsafe_b64encode(b"abc").decode()
    response = client.get(certificates_url, params={"pageToken": token})
    assert response.status_code == 400
