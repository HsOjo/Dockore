from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_docker
from app.core.security import get_current_token
from app.schemas.common import DeleteResult, IdsRequest, StatusResponse
from app.schemas.network import (
    ConnectRequest,
    DisconnectRequest,
    NetworkCreate,
    NetworkItem,
)
from app.services.docker.client import Docker

router = APIRouter(
    prefix="/networks",
    tags=["networks"],
    dependencies=[Depends(get_current_token)],
)


@router.get("", response_model=List[NetworkItem])
async def list_networks(docker: Docker = Depends(get_docker)):
    return await docker.network.list(greedy=True)


@router.get("/{id}", response_model=NetworkItem)
async def get_network(id: str, docker: Docker = Depends(get_docker)):
    item = await docker.network.item(id)
    if not item:
        raise HTTPException(status_code=404, detail="Network not found")
    return item


@router.post("", response_model=NetworkItem)
async def create_network(body: NetworkCreate, docker: Docker = Depends(get_docker)):
    data = body.model_dump()
    data["options"] = [o.model_dump() for o in body.options]
    return await docker.network.create(**data)


@router.delete("", response_model=DeleteResult)
async def delete_networks(body: IdsRequest, docker: Docker = Depends(get_docker)):
    failed = {}
    for id in body.ids:
        try:
            await docker.network.remove(id)
        except Exception as e:
            failed[id] = str(e)
    return DeleteResult(failed=failed)


@router.post("/{id}/connect", response_model=StatusResponse)
async def connect_network(
    id: str, body: ConnectRequest, docker: Docker = Depends(get_docker),
):
    await docker.network.connect(id, body.container_id, body.ipv4_address)
    return StatusResponse()


@router.post("/{id}/disconnect", response_model=StatusResponse)
async def disconnect_network(
    id: str,
    body: DisconnectRequest,
    force: bool = False,
    docker: Docker = Depends(get_docker),
):
    await docker.network.disconnect(id, body.container_id, force=force)
    return StatusResponse()
