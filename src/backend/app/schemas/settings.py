from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.core.settings_service import DEFAULT_SETTINGS


class SettingsData(BaseModel):
    model_config = ConfigDict(extra="allow")

    docker_host: str = DEFAULT_SETTINGS["docker_host"]
    docker_cli_path: str = DEFAULT_SETTINGS["docker_cli_path"]


class SettingsUpdate(BaseModel):
    docker_host: Optional[str] = None
    docker_cli_path: Optional[str] = None
