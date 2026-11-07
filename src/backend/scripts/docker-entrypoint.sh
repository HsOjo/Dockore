#!/bin/sh
set -e

cd /app

# Database initialization and Alembic migration run at app startup
# (see app/core/migrations.py, invoked from the FastAPI lifespan).

# Start the server. --no-sync: the image build already ran `uv sync`; re-syncing
# at runtime would require network access (build backend download) which is not
# guaranteed in restricted-network deployments.
exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000
