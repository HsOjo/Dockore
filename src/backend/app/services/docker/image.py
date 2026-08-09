import asyncio
from typing import Optional

from docker.errors import NotFound

from .convertors import HistoriesConvertor, ImageConvertor


class ImageService:
    """Async wrapper over docker-py's ImageCollection."""

    def __init__(self, collection, api=None):
        self._c = collection
        self._api = api

    convert = staticmethod(ImageConvertor.from_docker)

    async def _get(self, id: str):
        return await asyncio.to_thread(self._c.get, id)

    async def list(self, all: bool = False, verbose: bool = False):
        items = await asyncio.to_thread(self._c.list, all=all)
        return [ImageConvertor.from_docker(i, verbose) for i in items]

    async def item(self, id: str):
        try:
            item = await self._get(id)
        except NotFound:
            return None
        return ImageConvertor.from_docker(item, verbose=True)

    async def search(self, keyword: str):
        return await asyncio.to_thread(self._c.search, keyword)

    async def remove(self, id: str, tag_only: bool = False):
        await asyncio.to_thread(self._c.remove, id, noprune=tag_only)

    def pull_stream(self, name: str, tag: Optional[str]):
        """Sync generator of pull progress events; consumed by the pull task thread."""
        if not tag:
            tag = 'latest'
        if tag == '*':
            tag = None
        return self._api.pull(name, tag=tag, stream=True, decode=True)

    async def tag(self, id: str, name: str, tag: Optional[str]):
        return await asyncio.to_thread((await self._get(id)).tag, name, tag)

    async def history(self, id: str):
        histories = await asyncio.to_thread((await self._get(id)).history)
        return HistoriesConvertor.from_docker(histories)
