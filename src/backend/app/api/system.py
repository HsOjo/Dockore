import platform

from fastapi import APIRouter, Depends

from app.api.deps import get_docker
from app.core import config
from app.core.security import create_host_terminal_ticket, get_current_token
from app.core.version import APP_VERSION
from app.schemas.container import TerminalTicket
from app.schemas.system import ProjectInfo, SystemVersion
from app.services.cli import Docker

router = APIRouter(
    prefix="/system",
    tags=["system"],
    dependencies=[Depends(get_current_token)],
)


@router.get("/version", response_model=SystemVersion)
async def system_version(docker: Docker = Depends(get_docker)):
    uname = platform.uname()
    project = ProjectInfo(
        version=APP_VERSION,
        hostname=uname.node,
        python=platform.python_version(),
        os=uname.system,
        arch=uname.machine,
        kernel=uname.release,
    )
    return SystemVersion(project=project, docker=await docker.version())


@router.post("/terminal", response_model=TerminalTicket)
async def create_host_terminal_ticket_endpoint():
    expires = config.settings.dockore_terminal_expires
    ticket = create_host_terminal_ticket()
    return TerminalTicket(ticket=ticket, expires=expires)
