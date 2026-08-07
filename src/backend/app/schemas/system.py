from typing import Any, Dict

from pydantic import BaseModel


class ProjectInfo(BaseModel):
    version: str
    hostname: str
    python: str
    os: str
    arch: str
    kernel: str


class SystemVersion(BaseModel):
    project: ProjectInfo
    docker: Dict[str, Any]
