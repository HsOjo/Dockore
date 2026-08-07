from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.core.settings_service import DEFAULT_SETTINGS


class SettingsData(BaseModel):
    model_config = ConfigDict(extra="allow")

    docker_host: str = DEFAULT_SETTINGS["docker_host"]


class SettingsUpdate(BaseModel):
    docker_host: Optional[str] = None
