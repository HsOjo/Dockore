"""stack registrations table

Revision ID: 0002_stack_registrations
Revises: 0001_initial
Create Date: 2026-08-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import CHAR

revision: str = "0002_stack_registrations"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stack_registrations",
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("config_files", sa.String(length=2048), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("id", CHAR(length=36), nullable=False),
        sa.Column("create_time", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("update_time", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stack_registrations_name"), "stack_registrations", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_stack_registrations_name"), table_name="stack_registrations")
    op.drop_table("stack_registrations")
