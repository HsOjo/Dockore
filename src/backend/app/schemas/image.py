from typing import List, Optional

from pydantic import BaseModel, Field


class ExposedPort(BaseModel):
    port: int
    protocol: str


class ImageItem(BaseModel):
    id: str
    tags: List[str] = []
    author: str = ""
    create_time: str
    size: int = 0
    command: Optional[str] = None
    tty: Optional[bool] = None
    interactive: Optional[bool] = None
    architecture: Optional[str] = None
    os: Optional[str] = None
    ports: Optional[List[ExposedPort]] = None


class PullRequest(BaseModel):
    name: str
    tag: Optional[str] = None


class PullCreated(BaseModel):
    pull_id: str


class TagRequest(BaseModel):
    name: str
    tag: Optional[str] = None


class TagResult(BaseModel):
    success: bool


class HistoryItem(BaseModel):
    id: str
    created_by: str = ""
    created_time: str
    size: int = 0
    tags: Optional[List[str]] = None
    comment: Optional[str] = None


class ImageSearchItem(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    star_count: Optional[int] = None
    is_official: Optional[bool] = None
    is_automated: Optional[bool] = None


class DeleteImagesRequest(BaseModel):
    ids: List[str] = Field(min_length=1)
    tag_only: bool = False
