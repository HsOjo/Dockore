"""Database schema initialization and Alembic migration on startup.

Handles three database states:
  1. Fresh database: create tables and stamp at the current Alembic head.
  2. Existing database without Alembic tracking: compare the actual schema
     with the current model metadata. If it matches, stamp at head. If it is
     behind, stamp at the head's down_revision and upgrade to apply the
     missing changes.
  3. Tracked database: run pending Alembic migrations.
"""

import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from app.core.config import settings
from app.models import Base

logger = logging.getLogger(__name__)


def _alembic_ini_path() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller onedir: alembic.ini and alembic/ are bundled as data.
        return Path(sys._MEIPASS) / "alembic.ini"
    return Path(__file__).resolve().parent.parent.parent / "alembic.ini"


def _schema_matches_head(inspector, actual_tables, metadata) -> bool:
    """Return True if the database already has all tables and columns expected by the current model."""
    for table_name in metadata.tables:
        if table_name not in actual_tables:
            logger.info("Table missing: %s", table_name)
            return False
        actual_columns = {c["name"] for c in inspector.get_columns(table_name)}
        expected_columns = {c.name for c in metadata.tables[table_name].columns}
        missing = expected_columns - actual_columns
        if missing:
            logger.info("Table %s missing columns: %s", table_name, missing)
            return False
    return True


def run_migrations() -> None:
    """Create or upgrade the database schema to the current Alembic head.

    Must be called from a thread without a running event loop, because
    alembic/env.py drives the async engine with asyncio.run().
    """
    # Use a synchronous URL; the async app engine is not available here.
    db_url = settings.db_url.replace("+aiosqlite", "")
    engine = create_engine(db_url)
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        settings_exists = "settings" in tables
        alembic_exists = "alembic_version" in tables

        config = Config(str(_alembic_ini_path()))

        if not settings_exists:
            # Fresh database: create tables and stamp the current Alembic head.
            Base.metadata.create_all(engine)
            command.stamp(config, "head")
            logger.info("Database initialized with current schema and stamped at head.")
        elif not alembic_exists:
            # Existing database created before Alembic was introduced. Compare its
            # schema with the current model to decide whether it is already at head.
            if _schema_matches_head(inspector, tables, Base.metadata):
                command.stamp(config, "head")
                logger.info("Existing database schema matches head; stamped at head.")
            else:
                # Schema is behind head. Stamp at the head's down_revision and run
                # the upgrade so that Alembic applies the missing changes.
                script = ScriptDirectory.from_config(config)
                head_rev = script.get_revision("head")
                down_revision = head_rev.down_revision

                if down_revision:
                    # For merge points down_revision can be a tuple; use the first parent.
                    target = down_revision[0] if isinstance(down_revision, tuple) else down_revision
                    command.stamp(config, target)
                    logger.info("Existing database stamped at %s; upgrading to head.", target)

                command.upgrade(config, "head")
                logger.info("Database migrated to head.")
        else:
            # Tracked database: run pending migrations.
            command.upgrade(config, "head")
            logger.info("Database migrated to head.")
    finally:
        engine.dispose()
