#!/bin/sh
set -e

cd /app

# Database initialization and Alembic migration run at app startup
# (see app/core/migrations.py, invoked from the FastAPI lifespan).

# Start the server.
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
