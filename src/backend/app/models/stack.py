from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StackRegistration(Base):
    """User-confirmed stack directory: created by Dockore or imported from discovery."""

    __tablename__ = "stack_registrations"

    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    path: Mapped[str] = mapped_column(String(1024))
    config_files: Mapped[str] = mapped_column(String(2048), default="")
    source: Mapped[str] = mapped_column(String(16), default="created")
    # None = registered before this column existed, detect at runtime on list.
    is_git_repo: Mapped[Optional[bool]] = mapped_column(Boolean, default=None)
