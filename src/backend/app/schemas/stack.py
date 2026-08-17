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
    is_git_repo: bool = False


class StackMeta(BaseModel):
    cli_available: bool
    cli_version: Optional[str] = None
    cli_major: Optional[int] = None
    cli_binary: Optional[str] = None
    progress: bool = False
    container_mode: bool
    stacks_dir: str = ""
    git_available: bool = False


def _valid_stack_name(v: str) -> str:
    if not STACK_NAME_RE.match(v):
        raise ValueError(
            "name must match [a-z0-9][a-z0-9_-]* (compose project name)"
        )
    return v


class StackCreate(BaseModel):
    name: str
    content: str
    directory: Optional[str] = None
    env: Optional[str] = None

    @field_validator("name")
    @classmethod
    def valid_name(cls, v: str) -> str:
        return _valid_stack_name(v)


class GitCloneRequest(BaseModel):
    name: str
    repo_url: str
    branch: Optional[str] = None
    directory: Optional[str] = None

    @field_validator("name")
    @classmethod
    def valid_name(cls, v: str) -> str:
        return _valid_stack_name(v)


class GitCloneResult(BaseModel):
    name: str
    compose_files: List[str]
    env_templates: List[str]


class GitCreateRequest(BaseModel):
    name: str
    compose_path: str
    env_template_path: Optional[str] = None
    content: Optional[str] = None
    env: Optional[str] = None
    directory: Optional[str] = None

    @field_validator("name")
    @classmethod
    def valid_name(cls, v: str) -> str:
        return _valid_stack_name(v)


class GitCancelRequest(BaseModel):
    name: str
    directory: Optional[str] = None

    @field_validator("name")
    @classmethod
    def valid_name(cls, v: str) -> str:
        return _valid_stack_name(v)


class StackImport(BaseModel):
    name: str


class StackRegister(BaseModel):
    name: str
    path: str

    @field_validator("name")
    @classmethod
    def valid_name(cls, v: str) -> str:
        return _valid_stack_name(v)


class DownRequest(BaseModel):
    remove_volumes: bool = False


class DestroyRequest(BaseModel):
    remove_volumes: bool = False
    delete_files: bool = True


class FileContent(BaseModel):
    content: str


class StackFile(BaseModel):
    path: str
    content: str


class FileSaveResult(BaseModel):
    valid: bool
    error: Optional[str] = None


class TaskCreated(BaseModel):
    task_id: str


class BackupVolumeItem(BaseModel):
    key: str
    name: str
    archive: str
    size: int = 0


class BackupBindItem(BaseModel):
    source: str
    archive: str
    size: int = 0


class BackupSkippedItem(BaseModel):
    type: str
    ref: str
    reason: str


class BackupItem(BaseModel):
    id: str
    created_at: str
    size: int = 0
    was_running: bool = False
    compose_files: List[str] = []
    env_files: List[str] = []
    volumes: List[BackupVolumeItem] = []
    binds: List[BackupBindItem] = []
    skipped: List[BackupSkippedItem] = []


class StackTaskItem(BaseModel):
    id: str
    kind: str
    stack: str
    status: str
    returncode: Optional[int] = None
    error: Optional[str] = None
    started_at: float
    finished_at: Optional[float] = None
