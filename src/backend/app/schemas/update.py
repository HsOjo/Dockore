from pydantic import BaseModel


class UpdateAsset(BaseModel):
    name: str
    url: str


class UpdateCheckOut(BaseModel):
    current: str
    latest: str
    have_new: bool
    name: str
    tag_name: str
    published_at: str
    html_url: str
    body: str
    download_url: str | None = None
    assets: list[UpdateAsset] = []
