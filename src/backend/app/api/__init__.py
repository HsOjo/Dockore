from fastapi import APIRouter

from app.api import auth, container, image, network, settings, stack, system, volume
from app.schemas.common import StatusResponse

router = APIRouter()


@router.get("/health", response_model=StatusResponse, tags=["health"])
async def health():
    return StatusResponse()


router.include_router(auth.router)
router.include_router(container.router)
router.include_router(image.router)
router.include_router(network.router)
router.include_router(volume.router)
router.include_router(stack.router)
router.include_router(system.router)
router.include_router(settings.router)
