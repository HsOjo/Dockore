import asyncio
import threading
from typing import Optional

from docker import DockerClient

from .container import ContainerService
from .convertors import dict_to_lower, remove_empty_obj
from .image import ImageService
from .network import NetworkService
from .volume import VolumeService


class Docker:
    """Facade grouping the per-resource async services over one DockerClient."""

    def __init__(self, client: DockerClient):
        self._client = client
        self.container = ContainerService(client.containers)
        self.image = ImageService(client.images, client.api)
        self.network = NetworkService(client.networks)
        self.volume = VolumeService(client.volumes)

    @property
    def api(self):
        return self._client.api

    async def version(self):
        return await asyncio.to_thread(self._version)

    def _version(self):
        version = dict_to_lower(self._client.version())
        version['name'] = 'Docker'
        components = version.pop('components')
        for c in components:
            c.update(c.pop('details'))
        components.insert(0, version)
        result = {c.pop('name'): c for c in components}
        return remove_empty_obj(result)


_lock = threading.Lock()
_client: Optional[DockerClient] = None
_host: Optional[str] = None


def get_client(host: str) -> DockerClient:
    """Return a shared DockerClient for the host, rebuilding it when the host changes."""
    global _client, _host
    with _lock:
        if _client is None or _host != host:
            if _client is not None:
                try:
                    _client.close()
                except Exception:
                    pass
            _client = DockerClient(base_url=host)
            _host = host
        return _client
