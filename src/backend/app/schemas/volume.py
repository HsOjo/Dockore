from typing import Dict, List, Optional

from pydantic import BaseModel

from app.schemas.network import Option


class VolumeCreate(BaseModel):
    name: str
    driver: Optional[str] = None
    driver_opts: List[Option] = []


class VolumeItem(BaseModel):
    id: str
    name: str
    driver: Optional[str] = None
    mount_point: Optional[str] = None
    scope: Optional[str] = None
    create_time: str
    driver_opts: Optional[Dict[str, str]] = None
