from typing import Dict, List, Optional

from pydantic import BaseModel

from app.schemas.container import ContainerItem


class Option(BaseModel):
    key: str
    value: str


class NetworkCreate(BaseModel):
    name: str
    driver: str
    attachable: bool = True
    options: List[Option] = []
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    ip_range: Optional[str] = None


class NetworkItem(BaseModel):
    id: str
    name: str
    driver: Optional[str] = None
    scope: Optional[str] = None
    create_time: str
    container_num: int = 0
    subnet: Optional[str] = None
    gateway: Optional[str] = None
    ip_range: Optional[str] = None
    ipam_driver: Optional[str] = None
    internal: Optional[bool] = None
    attachable: Optional[bool] = None
    options: Optional[Dict[str, str]] = None
    containers: Optional[List[ContainerItem]] = None


class ConnectRequest(BaseModel):
    container_id: str
    ipv4_address: Optional[str] = None


class DisconnectRequest(BaseModel):
    container_id: str
