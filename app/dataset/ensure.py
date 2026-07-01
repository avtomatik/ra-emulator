from app.config.paths import SEEDS_DIR


def ensure_dataset_exists():
    required = ["users.json", "certificates.json", "cert_requests.json"]
    missing = [f for f in required if not (SEEDS_DIR / f).exists()]
    if missing:
        raise RuntimeError(
            f"Missing seed files: {missing}. "
            f"Run: python -m app.dataset.generate"
        )
