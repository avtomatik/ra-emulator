"""Storage setup, legacy import, and cached configuration lifecycle."""

import json

from app.config.settings import Settings, get_settings
from app.dataset.ensure import ensure_dataset_exists
from app.dataset.generate import build_dataset
from app.domain.models.certificate import Certificate
from app.storage.sqlite import SQLiteStore


def test_settings_cache_is_process_wide_and_clearable(monkeypatch, tmp_path):
    get_settings.cache_clear()
    monkeypatch.setenv(
        "RADP_EMULATOR_DATABASE_PATH", str(tmp_path / "a.sqlite3")
    )
    first = get_settings()
    assert first is get_settings()
    monkeypatch.setenv(
        "RADP_EMULATOR_DATABASE_PATH", str(tmp_path / "b.sqlite3")
    )
    assert get_settings() is first
    get_settings.cache_clear()
    assert get_settings().database_path == tmp_path / "b.sqlite3"
    get_settings.cache_clear()


def test_bootstrap_does_not_overwrite_existing_sqlite_data(tmp_path):
    settings = Settings(
        database_path=tmp_path / "emulator.sqlite3",
        certificate_folders=("alpha",),
    )
    store = SQLiteStore(settings.database_path)
    store.initialize()
    dataset = build_dataset(number=3, folders=("alpha",))
    store.replace_dataset(dataset)
    cert_before = store.all("certificates", Certificate)[0].id
    different_folders = settings.model_copy(
        update={"certificate_folders": ("beta",)}
    )
    ensure_dataset_exists(different_folders)
    assert store.count("certificates") == 3
    assert store.all("certificates", Certificate)[0].id == cert_before
    assert store.all("certificates", Certificate)[0].folder == "alpha"


def test_legacy_json_seed_files_import_once(monkeypatch, tmp_path):
    from app.dataset import ensure, loader

    seed_dir = tmp_path / "legacy"
    seed_dir.mkdir()
    dataset = build_dataset(number=4, folders=("oldfolder",))
    for name, rows in (
        ("users", dataset.users),
        ("certificates", dataset.certificates),
        ("cert_requests", dataset.cert_requests),
        ("rev_requests", dataset.rev_requests),
    ):
        payload = [
            row.model_dump(mode="json", exclude_none=True) for row in rows
        ]
        # Exercise legacy absence of the folder key.
        if name in ("certificates", "rev_requests"):
            for record in payload:
                record.pop("folder", None)
        (seed_dir / f"{name}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
    monkeypatch.setattr(ensure, "SEEDS_DIR", seed_dir)
    monkeypatch.setattr(loader, "SEEDS_DIR", seed_dir)
    settings = Settings(
        database_path=tmp_path / "out.sqlite3", certificate_folders=("legacy",)
    )
    store = ensure_dataset_exists(settings)
    assert store.count("certificates") == 4
    assert store.count("rev_requests") == 2
    assert all(
        item.folder == "legacy"
        for item in store.all("certificates", Certificate)
    )
    seed_dir.rename(tmp_path / "migrated_json")
    assert ensure_dataset_exists(settings).count("certificates") == 4
