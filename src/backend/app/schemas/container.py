from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.image import ImageItem


class PortMapping(BaseModel):
    port: int = Field(ge=1, le=65535)
    protocol: str = "tcp"
    listen_ip: str = "0.0.0.0"
    listen_port: int = Field(ge=1, le=65535)


class VolumeMapping(BaseModel):
    path: str
    bind: str
    mode: str = "rw"


class ContainerCreate(BaseModel):
    image: str
    command: str
    name: Optional[str] = None
    interactive: bool = False
    tty: bool = False
    privileged: bool = False
    ports: List[PortMapping] = []
    volumes: List[VolumeMapping] = []


class Mount(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    driver: Optional[str] = None
    mode: Optional[str] = None
    src: Optional[str] = None
    dest: Optional[str] = None


class ContainerNetwork(BaseModel):
    ip: Optional[str] = None
    prefix: Optional[int] = None
    gateway: Optional[str] = None
    mac_address: Optional[str] = None
    ports: Optional[List[PortMapping]] = None


class ContainerItem(BaseModel):
    id: str
    name: str
    image: ImageItem
    create_time: str
    status: str
    command: Optional[str] = None
    tty: Optional[bool] = None
    interactive: Optional[bool] = None
    network: Optional[ContainerNetwork] = None
    mounts: Optional[List[Mount]] = None


class ContainerDiff(BaseModel):
    add: List[str] = []
    change: List[str] = []
    delete: List[str] = []
    other: List[str] = []


class RenameRequest(BaseModel):
    name: str


class CommitRequest(BaseModel):
    name: str
    tag: Optional[str] = None
    message: Optional[str] = None
    author: Optional[str] = None


class ExecRequest(BaseModel):
    command: str
    interactive: bool = True
    tty: bool = True
    privileged: bool = False


class ExecResult(BaseModel):
    exit_code: int
    output: str


class TerminalRequest(BaseModel):
    command: Optional[str] = None


class TerminalTicket(BaseModel):
    ticket: str
    expires: int
