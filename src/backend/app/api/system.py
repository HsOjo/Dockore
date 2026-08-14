import os
import platform
import subprocess

import psutil
from fastapi import APIRouter, Depends

from app.api.deps import get_docker
from app.core import config
from app.core.security import create_host_terminal_ticket, get_current_token
from app.core.version import APP_VERSION
from app.schemas.container import TerminalTicket
from app.schemas.system import ProjectInfo, SystemVersion
from app.services.cli import Docker
from app.services.metrics import HOST_PROC_ENV

router = APIRouter(
    prefix="/system",
    tags=["system"],
    dependencies=[Depends(get_current_token)],
)


def _cpu_model() -> str:
    system = platform.system()
    if system == "Linux":
        proc = os.environ.get(HOST_PROC_ENV, "/proc")
        try:
            with open(f"{proc}/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
    elif system == "Darwin":
        try:
            return subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True,
            ).strip()
        except Exception:
            pass
    return platform.processor()


@router.get("/version", response_model=SystemVersion)
async def system_version(docker: Docker = Depends(get_docker)):
    uname = platform.uname()
    cpu_count = psutil.cpu_count() or 0
    cpu_model = _cpu_model()
    project = ProjectInfo(
        version=APP_VERSION,
        hostname=uname.node,
        python=platform.python_version(),
        os=uname.system,
        arch=uname.machine,
        kernel=uname.release,
        cpu=f"{cpu_count} x {cpu_model}" if cpu_model else f"{cpu_count} CPU(s)",
    )
    return SystemVersion(project=project, docker=await docker.version())


@router.post("/terminal", response_model=TerminalTicket)
async def create_host_terminal_ticket_endpoint():
    expires = config.settings.dockore_terminal_expires
    ticket = create_host_terminal_ticket()
    return TerminalTicket(ticket=ticket, expires=expires)
