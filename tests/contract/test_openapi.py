import json


def test_openapi_is_current(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    with open("openapi.json", encoding="utf-8") as file:
        committed = json.load(file)
    assert committed == response.json()
