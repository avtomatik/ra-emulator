"""Non-destructive first-start setup, including migration of older JSON seeds."""

import logging

from app.config.paths import SEEDS_DIR
from app.config.settings import Settings
from app.dataset.loader import load_dataset
from app.storage.sqlite import SQLiteStore

log = logging.getLogger(__name__)


def ensure_dataset_exists(settings: Settings) -> SQLiteStore:
    store = SQLiteStore(settings.database_path)
    store.initialize()
    if store.count("users"):
        return store
    required = ("users.json", "certificates.json", "cert_requests.json")
    if all((SEEDS_DIR / name).is_file() for name in required):
        log.info(
            "Importing legacy JSON seed files into %s", settings.database_path
        )
        store.replace_dataset(
            load_dataset(default_folder=settings.certificate_folders[0])
        )
    else:
        # Auto-bootstrap preserves the original one-command local development experience.
        # Unlike the old Docker entrypoint, restarts NEVER regenerate existing data.
        from app.dataset.generate import build_dataset

        log.info(
            "Creating initial SQLite seed dataset at %s",
            settings.database_path,
        )
        store.replace_dataset(
            build_dataset(folders=settings.certificate_folders)
        )
    return store
