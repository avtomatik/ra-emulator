from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SEEDS_DIR = BASE_DIR / "data" / "seeds"
SEEDS_DIR.mkdir(parents=True, exist_ok=True)
