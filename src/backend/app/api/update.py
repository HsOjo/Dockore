from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import settings_service
from app.core.database import get_db
from app.core.security import get_current_token
from app.core.settings_service import proxy_from_settings
from app.core.updater import check_update
from app.core.version import APP_VERSION
from app.schemas.update import UpdateCheckOut

router = APIRouter(
    tags=["update"],
    dependencies=[Depends(get_current_token)],
)


@router.get("/update", response_model=UpdateCheckOut)
async def check_for_update(
    force: bool = False, session: AsyncSession = Depends(get_db)
):
    all_settings = await settings_service.get_all(session)
    proxy = proxy_from_settings(all_settings, "outbound").url
    try:
        release, have_new = await check_update(force=force, proxy=proxy)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return UpdateCheckOut(
        current=APP_VERSION,
        latest=release.tag_name,
        have_new=have_new,
        name=release.name,
        tag_name=release.tag_name,
        published_at=release.published_at,
        html_url=release.html_url,
        body=release.body,
        download_url=release.download_url,
        assets=release.assets,
    )
