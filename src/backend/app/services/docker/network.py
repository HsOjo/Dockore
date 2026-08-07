import asyncio
from typing import Optional

from docker.errors import NotFound
from docker.types import IPAMConfig, IPAMPool

from .convertors import NetworkConvertor, OptionConvertor


class NetworkService:
    """Async wrapper over docker-py's NetworkCollection."""

    def __init__(self, collection):
        self._c = collection

    async def _get(self, id: str):
        return await asyncio.to_thread(self._c.get, id)

    async def list(self, verbose: bool = False, **kwargs):
        items = await asyncio.to_thread(self._c.list, **kwargs)
        return [NetworkConvertor.from_docker(i, verbose) for i in items]

    async def item(self, id: str):
        try:
            item = await self._get(id)
        except NotFound:
            return None
        return NetworkConvertor.from_docker(item, verbose=True)

    async def remove(self, id: str):
        await asyncio.to_thread((await self._get(id)).remove)

    async def create(self, name, driver, attachable=True, options=None,
                     subnet=None, gateway=None, ip_range=None):
        ipam_config = None
        if subnet:
            ipam_config = IPAMConfig(pool_configs=[IPAMPool(
                subnet=subnet,
                gateway=gateway,
                iprange=ip_range,
            )])
        item = await asyncio.to_thread(
            self._c.create,
            name, driver, attachable=attachable,
            options=OptionConvertor.to(options or []), ipam=ipam_config,
        )
        return NetworkConvertor.from_docker(item, verbose=True)

    async def connect(self, id: str, container_id: str, ipv4_address: Optional[str] = None):
        await asyncio.to_thread(
            (await self._get(id)).connect, container_id, ipv4_address=ipv4_address,
        )

    async def disconnect(self, id: str, container_id: str, force: bool = False):
        await asyncio.to_thread((await self._get(id)).disconnect, container_id, force=force)
