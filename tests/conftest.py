import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


@pytest.fixture
def slow_client() -> TestClient:
    settings = Settings(latency_ms=100)
    return TestClient(create_app(settings))


@pytest.fixture
def certificates_url() -> str:
    return "/api/ra/certificates"


@pytest.fixture
def cert_requests_url() -> str:
    return "/api/ra/certRequests"


@pytest.fixture
def users_url() -> str:
    return "/api/ra/users"
