from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.api.deps import get_docker
from app.core.config import settings
from app.core.security import create_terminal_ticket, get_current_token
from app.core.validators import validate_since_until
from app.schemas.common import DeleteResult, IdsRequest, StatusResponse
from app.schemas.container import (
    CommitRequest,
    ContainerCreate,
    ContainerDiff,
    ContainerItem,
    ExecRequest,
    ExecResult,
    RenameRequest,
    TerminalRequest,
    TerminalTicket,
)
from app.schemas.image import ImageItem
from app.services.cli import Docker

router = APIRouter(
    prefix="/containers",
    tags=["containers"],
    dependencies=[Depends(get_current_token)],
)


@router.get("", response_model=list[ContainerItem])
async def list_containers(all: bool = False, docker: Docker = Depends(get_docker)):
    return await docker.container.list(all=all)


@router.get("/{id}", response_model=ContainerItem)
async def get_container(id: str, docker: Docker = Depends(get_docker)):
    item = await docker.container.item(id)
    if not item:
        raise HTTPException(status_code=404, detail="Container not found")
    return item


@router.post("", response_model=ContainerItem)
async def create_container(
    body: ContainerCreate,
    run: bool = False,
    docker: Docker = Depends(get_docker),
):
    data = body.model_dump()
    ports = [p.model_dump() for p in body.ports] or None
    volumes = [v.model_dump() for v in body.volumes] or None
    data.update(ports=ports, volumes=volumes)
    if run:
        return await docker.container.run(**data)
    return await docker.container.create(**data)


@router.delete("", response_model=DeleteResult)
async def delete_containers(body: IdsRequest, docker: Docker = Depends(get_docker)):
    failed = {}
    for id in body.ids:
        try:
            await docker.container.remove(id)
        except Exception as e:
            failed[id] = str(e)
    return DeleteResult(failed=failed)


@router.post("/{id}/start", response_model=StatusResponse)
async def start_container(id: str, docker: Docker = Depends(get_docker)):
    await docker.container.start(id)
    return StatusResponse()


@router.post("/{id}/stop", response_model=StatusResponse)
async def stop_container(
    id: str,
    timeout: Optional[int] = Query(None),
    docker: Docker = Depends(get_docker),
):
    await docker.container.stop(id, timeout)
    return StatusResponse()


@router.post("/{id}/restart", response_model=StatusResponse)
async def restart_container(
    id: str,
    timeout: Optional[int] = Query(None),
    docker: Docker = Depends(get_docker),
):
    await docker.container.restart(id, timeout)
    return StatusResponse()


@router.post("/{id}/rename", response_model=StatusResponse)
async def rename_container(
    id: str, body: RenameRequest, docker: Docker = Depends(get_docker),
):
    await docker.container.rename(id, body.name)
    return StatusResponse()


@router.get("/{id}/logs", response_class=PlainTextResponse)
async def container_logs(
    id: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
    docker: Docker = Depends(get_docker),
):
    since, until = validate_since_until(since, until)
    return await docker.container.logs(id, since=since, until=until)


@router.get("/{id}/diff", response_model=ContainerDiff)
async def container_diff(id: str, docker: Docker = Depends(get_docker)):
    return await docker.container.diff(id)


@router.post("/{id}/commit", response_model=ImageItem)
async def commit_container(
    id: str, body: CommitRequest, docker: Docker = Depends(get_docker),
):
    return await docker.container.commit(id, **body.model_dump())


@router.post("/{id}/exec", response_model=ExecResult)
async def exec_container(
    id: str, body: ExecRequest, docker: Docker = Depends(get_docker),
):
    return await docker.container.exec(id, **body.model_dump())


@router.post("/{id}/terminal", response_model=TerminalTicket)
async def create_terminal_ticket_endpoint(
    id: str, body: TerminalRequest, docker: Docker = Depends(get_docker),
):
    item = await docker.container.item(id)
    if not item:
        raise HTTPException(status_code=404, detail="Container not found")
    expires = settings.dockore_terminal_expires
    ticket = create_terminal_ticket(id, body.command)
    return TerminalTicket(ticket=ticket, expires=expires)
