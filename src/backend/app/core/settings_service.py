from dataclasses import dataclass
from typing import Mapping, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Setting

DEFAULT_SETTINGS = {
    "docker_host": "unix:///var/run/docker.sock",
    "docker_cli_path": "auto",
    "http_proxy": "",
    "https_proxy": "",
    "no_proxy": "",
    "proxy_cli": "true",
    "proxy_outbound": "true",
}

_TRUTHY = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ProxyConfig:
    http_proxy: str = ""
    https_proxy: str = ""
    no_proxy: str = ""

    def apply(self, env: dict[str, str]) -> None:
        """Inject proxy vars into a subprocess env; both cases for CLI compat."""
        if self.http_proxy:
            env["HTTP_PROXY"] = env["http_proxy"] = self.http_proxy
        if self.https_proxy:
            env["HTTPS_PROXY"] = env["https_proxy"] = self.https_proxy
        if self.no_proxy:
            env["NO_PROXY"] = env["no_proxy"] = self.no_proxy

    @property
    def url(self) -> Optional[str]:
        """Single proxy URL for HTTP clients (e.g. httpx); None when unset."""
        return self.https_proxy or self.http_proxy or None


def proxy_from_settings(all_settings: Mapping[str, str], scope: str) -> ProxyConfig:
    """Resolve the effective proxy for a scope ("cli" or "outbound").

    Returns an empty config when the scope toggle is off, so page settings
    only override inherited env vars when explicitly enabled.
    """
    if all_settings.get(f"proxy_{scope}", "true").strip().lower() not in _TRUTHY:
        return ProxyConfig()
    return ProxyConfig(
        http_proxy=all_settings.get("http_proxy", ""),
        https_proxy=all_settings.get("https_proxy", ""),
        no_proxy=all_settings.get("no_proxy", ""),
    )


async def get_all(session: AsyncSession) -> dict[str, str]:
    """Return all settings merged with defaults; env vars take priority over the DB."""
    result = dict(DEFAULT_SETTINGS)
    rows = await session.execute(select(Setting))
    for row in rows.scalars():
        result[row.key] = row.value
    if settings.dockore_docker_host:
        result["docker_host"] = settings.dockore_docker_host
    return result


async def set_many(session: AsyncSession, data: dict[str, str]) -> None:
    rows = await session.execute(select(Setting).where(Setting.key.in_(data.keys())))
    existed = {row.key: row for row in rows.scalars()}
    for key, value in data.items():
        if key in existed:
            existed[key].value = value
        else:
            session.add(Setting(key=key, value=value))
    await session.commit()
