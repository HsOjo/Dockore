from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.settings_service import DEFAULT_SETTINGS


class SettingsData(BaseModel):
    model_config = ConfigDict(extra="allow")

    docker_host: str = DEFAULT_SETTINGS["docker_host"]
    docker_cli_path: str = DEFAULT_SETTINGS["docker_cli_path"]
    http_proxy: str = DEFAULT_SETTINGS["http_proxy"]
    https_proxy: str = DEFAULT_SETTINGS["https_proxy"]
    no_proxy: str = DEFAULT_SETTINGS["no_proxy"]
    proxy_cli: bool = True
    proxy_outbound: bool = True
    metrics_interval: int = int(DEFAULT_SETTINGS["metrics_interval"])


class SettingsUpdate(BaseModel):
    docker_host: Optional[str] = None
    docker_cli_path: Optional[str] = None
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: Optional[str] = None
    proxy_cli: Optional[bool] = None
    proxy_outbound: Optional[bool] = None
    metrics_interval: Optional[int] = Field(default=None, ge=1, le=60)
