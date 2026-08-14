from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ProjectInfo(BaseModel):
    version: str
    hostname: str
    python: str
    os: str
    arch: str
    kernel: str
    cpu: str


class SystemVersion(BaseModel):
    project: ProjectInfo
    docker: Dict[str, Any]


class UsageGauge(BaseModel):
    total: int
    used: int
    percent: float


class DiskGauge(UsageGauge):
    path: str


class NetRates(BaseModel):
    in_rate: Optional[float] = None
    out_rate: Optional[float] = None


class DiskIORates(BaseModel):
    read_rate: Optional[float] = None
    write_rate: Optional[float] = None


class SystemMetrics(BaseModel):
    error: Optional[str] = None
    timestamp: float = 0
    cpu_percent: float = 0
    cpu_count: int = 0
    io_delay: Optional[float] = None
    memory: Optional[UsageGauge] = None
    swap: Optional[UsageGauge] = None
    disk: Optional[DiskGauge] = None
    load_avg: Optional[List[float]] = None
    net: Optional[NetRates] = None
    disk_io: Optional[DiskIORates] = None
    uptime: float = 0
