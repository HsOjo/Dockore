from typing import Dict, List

from pydantic import BaseModel, Field


class IdsRequest(BaseModel):
    ids: List[str] = Field(min_length=1)


class DeleteResult(BaseModel):
    """Failed ids mapped to their error message; empty means fully succeeded."""
    failed: Dict[str, str] = {}


class StatusResponse(BaseModel):
    status: str = "ok"


class ValidateResponse(BaseModel):
    valid: bool = True
