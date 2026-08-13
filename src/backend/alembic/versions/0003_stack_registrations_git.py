"""stack registrations is_git_repo column

Revision ID: 0003_stack_registrations_git
Revises: 0002_stack_registrations
Create Date: 2026-08-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_stack_registrations_git"
down_revision: Union[str, None] = "0002_stack_registrations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable on purpose: NULL marks pre-existing rows so the API falls back
    # to a runtime .git check instead of assuming False.
    op.add_column(
        "stack_registrations", sa.Column("is_git_repo", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("stack_registrations", "is_git_repo")
