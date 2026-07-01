def test_list_users_returns_first_page(client, users_url):
    response = client.get(users_url)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 20
    assert "_links" in body
    assert "next" in body["_links"]


def test_user_summary_contains_expected_fields(client, users_url):
    response = client.get(users_url)
    user = response.json()["items"][0]
    assert {
        "id",
        "nameAttributes",
        "createdWhen",
    }.issubset(user)
    assert "distinguishedName" in user


def test_get_user_returns_user(client, users_url):
    response = client.get(users_url)
    user_id = response.json()["items"][0]["id"]
    response = client.get(f"{users_url}/{user_id}")
    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_get_unknown_user_returns_404(client, users_url):
    response = client.get(f"{users_url}/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
