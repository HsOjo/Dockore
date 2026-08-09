from fastapi import APIRouter, Depends

from app.core.security import get_current_token
from app.schemas.common import ValidateResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/validate", response_model=ValidateResponse)
async def validate(_: str = Depends(get_current_token)):
    return ValidateResponse()
