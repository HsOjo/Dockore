from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings_service
from app.core.database import get_db
from app.core.security import get_current_token
from app.schemas.settings import SettingsData, SettingsUpdate

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_token)],
)


@router.get("", response_model=SettingsData)
async def get_settings(session: AsyncSession = Depends(get_db)):
    return await settings_service.get_all(session)


@router.put("", response_model=SettingsData)
async def update_settings(
    body: SettingsUpdate, session: AsyncSession = Depends(get_db),
):
    data = {
        k: str(v).lower() if isinstance(v, bool) else v
        for k, v in body.model_dump().items()
        if v is not None
    }
    if data:
        await settings_service.set_many(session, data)
    return await settings_service.get_all(session)
