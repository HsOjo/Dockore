#!/bin/sh
set -e

cd /app

# Initialize or migrate the database before starting the server.
# This handles three states:
#   1. Fresh database: create tables and stamp at the current Alembic head.
#   2. Existing database without Alembic tracking: compare the actual schema
#      with the current model metadata. If it matches, stamp at head. If it is
#      behind, stamp at the head's down_revision and upgrade to apply the
#      missing changes.
#   3. Tracked database: run pending Alembic migrations.
uv run python - <<'PY'
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from app.core.config import settings
from app.models import Base

# Use a synchronous URL because this script runs before the async app starts.
db_url = settings.db_url.replace("+aiosqlite", "")
engine = create_engine(db_url)


def schema_matches_head(inspector, actual_tables, metadata):
    """Return True if the database already has all tables and columns expected by the current model."""
    for table_name in metadata.tables:
        if table_name not in actual_tables:
            print(f"Table missing: {table_name}")
            return False
        actual_columns = {c["name"] for c in inspector.get_columns(table_name)}
        expected_columns = {c.name for c in metadata.tables[table_name].columns}
        missing = expected_columns - actual_columns
        if missing:
            print(f"Table {table_name} missing columns: {missing}")
            return False
    return True


try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    settings_exists = "settings" in tables
    alembic_exists = "alembic_version" in tables

    config = Config("/app/alembic.ini")

    if not settings_exists:
        # Fresh database: create tables and stamp the current Alembic head.
        Base.metadata.create_all(engine)
        command.stamp(config, "head")
        print("Database initialized with current schema and stamped at head.")
    elif not alembic_exists:
        # Existing database created before Alembic was introduced.  Compare its
        # schema with the current model to decide whether it is already at head.
        if schema_matches_head(inspector, tables, Base.metadata):
            command.stamp(config, "head")
            print("Existing database schema matches head; stamped at head.")
        else:
            # Schema is behind head.  Stamp at the head's down_revision and run
            # the upgrade so that Alembic applies the missing changes.
            script = ScriptDirectory.from_config(config)
            head_rev = script.get_revision("head")
            down_revision = head_rev.down_revision

            if down_revision:
                # For merge points down_revision can be a tuple; use the first parent.
                target = down_revision[0] if isinstance(down_revision, tuple) else down_revision
                command.stamp(config, target)
                print(f"Existing database stamped at {target} and will be upgraded to head.")
            else:
                # Head is the first revision; it creates the schema itself.
                pass

            command.upgrade(config, "head")
            print("Database migrated to head.")
    else:
        # Tracked database: run pending migrations.
        command.upgrade(config, "head")
        print("Database migrated to head.")
finally:
    engine.dispose()
PY

# Start the server.
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
