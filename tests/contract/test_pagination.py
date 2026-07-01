def test_certificate_pagination_returns_20_items(client, certificates_url):
    response = client.get(certificates_url)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 20


def test_certificate_pagination_next_link_can_be_followed(
    client, certificates_url
):
    response = client.get(certificates_url)
    first_page = response.json()
    next_href = first_page["_links"]["next"]["href"]
    response = client.get(next_href)
    assert response.status_code == 200
    second_page = response.json()
    assert len(second_page["items"]) == 20


def test_pagination_does_not_duplicate_items(client, certificates_url):
    response = client.get(certificates_url)
    first_page = response.json()
    first_ids = [item["id"] for item in first_page["items"]]
    response = client.get(first_page["_links"]["next"]["href"])
    second_page = response.json()
    second_ids = [item["id"] for item in second_page["items"]]
    assert set(first_ids).isdisjoint(second_ids)


def test_final_page_has_no_links(client, certificates_url):
    response = client.get(certificates_url)
    while response.json().get("_links"):
        response = client.get(response.json()["_links"]["next"]["href"])
    assert response.status_code == 200
    final_page = response.json()
    assert len(final_page["items"]) == 20
    assert "_links" not in final_page
