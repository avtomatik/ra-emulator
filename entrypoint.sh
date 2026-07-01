#!/bin/sh
set -e

echo "Running dataset seed generation..."
python -m app.dataset.generate

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
