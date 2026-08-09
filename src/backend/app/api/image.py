import asyncio
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_docker
from app.core.security import get_current_token
from app.schemas.common import DeleteResult
from app.schemas.image import (
    DeleteImagesRequest,
    HistoryItem,
    ImageItem,
    ImageSearchItem,
    PullCreated,
    PullRequest,
    TagRequest,
    TagResult,
)
from app.services.docker.client import Docker
from app.services.pull_task import pull_manager

router = APIRouter(
    prefix="/images",
    tags=["images"],
    dependencies=[Depends(get_current_token)],
)


@router.get("", response_model=List[ImageItem])
async def list_images(all: bool = False, docker: Docker = Depends(get_docker)):
    return await docker.image.list(all=all)


@router.get("/{id}", response_model=ImageItem)
async def get_image(id: str, docker: Docker = Depends(get_docker)):
    item = await docker.image.item(id)
    if not item:
        raise HTTPException(status_code=404, detail="Image not found")
    return item


@router.delete("", response_model=DeleteResult)
async def delete_images(body: DeleteImagesRequest, docker: Docker = Depends(get_docker)):
    failed = {}
    for id in body.ids:
        try:
            await docker.image.remove(id, tag_only=body.tag_only)
        except Exception as e:
            failed[id] = str(e)
    return DeleteResult(failed=failed)


@router.post("/pull", response_model=PullCreated)
async def pull_image(body: PullRequest, docker: Docker = Depends(get_docker)):
    pull_id = pull_manager.start(
        docker, body.name, body.tag, asyncio.get_running_loop(),
    )
    return PullCreated(pull_id=pull_id)


@router.post("/{id}/tag", response_model=TagResult)
async def tag_image(id: str, body: TagRequest, docker: Docker = Depends(get_docker)):
    success = await docker.image.tag(id, body.name, body.tag)
    return TagResult(success=bool(success))


@router.get("/{id}/history", response_model=List[HistoryItem])
async def image_history(id: str, docker: Docker = Depends(get_docker)):
    return await docker.image.history(id)


@router.get("/search/{keyword}", response_model=List[ImageSearchItem])
async def search_images(keyword: str, docker: Docker = Depends(get_docker)):
    return await docker.image.search(keyword)
