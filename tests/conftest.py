"""Isolation: every HTTP test gets its own copy of one synthetic SQLite seed."""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.dataset.generate import build_dataset
from app.main import create_app
from app.storage.sqlite import SQLiteStore


@pytest.fixture(scope="session")
def seed_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("seed") / "base.sqlite3"
    store = SQLiteStore(path)
    store.initialize()
    store.replace_dataset(build_dataset())
    return path


@pytest.fixture
def settings(seed_db: Path, tmp_path: Path) -> Settings:
    path = tmp_path / "emulator.sqlite3"
    # SQLite backup is safe even with an existing WAL journal.
    with (
        sqlite3.connect(seed_db) as source,
        sqlite3.connect(path) as destination,
    ):
        source.backup(destination)
    return Settings(database_path=path)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


@pytest.fixture
def slow_client(settings: Settings) -> TestClient:
    return TestClient(
        create_app(settings.model_copy(update={"latency_ms": 100}))
    )


@pytest.fixture
def certificates_url() -> str:
    return "/api/ra/certificates"


@pytest.fixture
def cert_requests_url() -> str:
    return "/api/ra/certRequests"


@pytest.fixture
def rev_requests_url() -> str:
    return "/api/ra/revRequests"


@pytest.fixture
def users_url() -> str:
    return "/api/ra/users"
