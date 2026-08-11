from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.services.stack import STACK_NAME_RE


class StackContainerItem(BaseModel):
    id: str
    name: str
    service: str = ""
    state: str = ""
    status: str = ""


class StackItem(BaseModel):
    name: str
    status: str
    running: int = 0
    total: int = 0
    containers: List[StackContainerItem] = []
    working_dir: str = ""
    config_files: List[str] = []
    registered: bool = False
    source: str = "discovered"
    file_accessible: bool = False


class StackMeta(BaseModel):
    cli_available: bool
    cli_version: Optional[str] = None
    cli_major: Optional[int] = None
    cli_binary: Optional[str] = None
    progress: bool = False
    container_mode: bool
    stacks_dir: str = ""


class StackCreate(BaseModel):
    name: str
    content: str
    directory: Optional[str] = None
    env: Optional[str] = None

    @field_validator("name")
    @classmethod
    def valid_name(cls, v: str) -> str:
        if not STACK_NAME_RE.match(v):
            raise ValueError(
                "name must match [a-z0-9][a-z0-9_-]* (compose project name)"
            )
        return v


class StackImport(BaseModel):
    name: str


class DownRequest(BaseModel):
    remove_volumes: bool = False


class DestroyRequest(BaseModel):
    remove_volumes: bool = False
    delete_files: bool = True


class TaskCreated(BaseModel):
    task_id: str


class StackTaskItem(BaseModel):
    id: str
    kind: str
    stack: str
    status: str
    returncode: Optional[int] = None
    error: Optional[str] = None
    started_at: float
    finished_at: Optional[float] = None
