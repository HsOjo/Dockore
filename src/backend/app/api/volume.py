from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_docker
from app.core.security import get_current_token
from app.schemas.common import DeleteResult, IdsRequest
from app.schemas.volume import VolumeCreate, VolumeItem
from app.services.cli import Docker

router = APIRouter(
    prefix="/volumes",
    tags=["volumes"],
    dependencies=[Depends(get_current_token)],
)


@router.get("", response_model=List[VolumeItem])
async def list_volumes(docker: Docker = Depends(get_docker)):
    return await docker.volume.list()


@router.get("/{id}", response_model=VolumeItem)
async def get_volume(id: str, docker: Docker = Depends(get_docker)):
    item = await docker.volume.item(id)
    if not item:
        raise HTTPException(status_code=404, detail="Volume not found")
    return item


@router.post("", response_model=VolumeItem)
async def create_volume(body: VolumeCreate, docker: Docker = Depends(get_docker)):
    data = body.model_dump()
    data["driver_opts"] = [o.model_dump() for o in body.driver_opts]
    return await docker.volume.create(**data)


@router.delete("", response_model=DeleteResult)
async def delete_volumes(body: IdsRequest, docker: Docker = Depends(get_docker)):
    failed = {}
    for id in body.ids:
        try:
            await docker.volume.remove(id)
        except Exception as e:
            failed[id] = str(e)
    return DeleteResult(failed=failed)
