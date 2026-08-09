import asyncio
from typing import Optional

from docker.errors import NotFound

from .convertors import OptionConvertor, VolumeConvertor


class VolumeService:
    """Async wrapper over docker-py's VolumeCollection."""

    def __init__(self, collection):
        self._c = collection

    async def _get(self, id: str):
        return await asyncio.to_thread(self._c.get, id)

    async def list(self, verbose: bool = False, **kwargs):
        items = await asyncio.to_thread(self._c.list, **kwargs)
        return [VolumeConvertor.from_docker(i, verbose) for i in items]

    async def item(self, id: str):
        try:
            item = await self._get(id)
        except NotFound:
            return None
        return VolumeConvertor.from_docker(item, verbose=True)

    async def remove(self, id: str):
        await asyncio.to_thread((await self._get(id)).remove)

    async def create(self, name, driver: Optional[str] = None, driver_opts=None):
        item = await asyncio.to_thread(
            self._c.create,
            name, driver=driver, driver_opts=OptionConvertor.to(driver_opts or []),
        )
        return VolumeConvertor.from_docker(item, verbose=True)
