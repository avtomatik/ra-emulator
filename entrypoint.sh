#!/bin/sh
set -eu

# First startup auto-seeds; following starts preserve the SQLite database.
# To deliberately replace the dataset: python -m app.dataset.generate
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
