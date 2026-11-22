import json


def _normalize_bytes_schema(schema):
    """Ignore known FastAPI 0.128 vs 0.138 OpenAPI bytes encoding difference."""
    for name, field in (
        ("CertificateDetailDTO", "rawCertificate"),
        ("CertificateRequestDetailDTO", "rawRequest"),
        ("RevocationRequestDetailDTO", "rawRequest"),
    ):
        prop = schema["components"]["schemas"][name]["properties"][field]
        encoding = prop["anyOf"][0]
        if encoding.pop("format", None) == "binary":
            encoding["contentMediaType"] = "application/octet-stream"
    return schema


def test_openapi_is_current(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    with open("openapi.json", encoding="utf-8") as file:
        committed = json.load(file)
    assert _normalize_bytes_schema(committed) == _normalize_bytes_schema(
        response.json()
    )
