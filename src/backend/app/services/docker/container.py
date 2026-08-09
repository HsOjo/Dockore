import asyncio
from datetime import datetime
from typing import Optional, Union

from docker.errors import NotFound

from .convertors import ContainerConvertor, PortMappingConvertor, VolumesMappingConvertor


def parse_ts(value: Optional[Union[str, int]]) -> Optional[Union[int, datetime]]:
    """Parse a since/until timestamp: epoch digits stay ints, otherwise ISO format."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if value.isdigit():
        return int(value)
    return datetime.fromisoformat(value)


class ContainerService:
    """Async wrapper over docker-py's ContainerCollection."""

    def __init__(self, collection, api=None):
        self._c = collection
        self._api = api

    async def _get(self, id: str):
        return await asyncio.to_thread(self._c.get, id)

    async def list(self, all: bool = False, verbose: bool = False):
        items = await asyncio.to_thread(self._c.list, all=all)
        return [ContainerConvertor.from_docker(i, verbose) for i in items]

    async def item(self, id: str):
        try:
            item = await self._get(id)
        except NotFound:
            return None
        return ContainerConvertor.from_docker(item, verbose=True)

    async def remove(self, id: str):
        await asyncio.to_thread((await self._get(id)).remove)

    async def create(self, name, image, command, interactive=False, tty=False,
                     ports=None, volumes=None):
        item = await asyncio.to_thread(
            self._c.create,
            image, command, name=name, stdin_open=interactive, tty=tty,
            ports=PortMappingConvertor.to_docker(ports),
            volumes=VolumesMappingConvertor.to_docker(volumes or []),
        )
        return ContainerConvertor.from_docker(item, verbose=True)

    async def run(self, name, image, command, interactive=False, tty=False,
                  ports=None, volumes=None):
        item = await asyncio.to_thread(
            self._c.run,
            image, command, name=name, stdin_open=interactive, tty=tty, detach=True,
            ports=PortMappingConvertor.to_docker(ports),
            volumes=VolumesMappingConvertor.to_docker(volumes or []),
        )
        return ContainerConvertor.from_docker(item, verbose=True)

    async def start(self, id: str):
        await asyncio.to_thread((await self._get(id)).start)

    async def stop(self, id: str, timeout: Optional[int] = None):
        await asyncio.to_thread((await self._get(id)).stop, timeout=timeout)

    async def restart(self, id: str, timeout: Optional[int] = None):
        await asyncio.to_thread((await self._get(id)).restart, timeout=timeout)

    async def rename(self, id: str, name: str):
        await asyncio.to_thread((await self._get(id)).rename, name)

    async def exec(self, id: str, command, interactive=False, tty=False,
                   privileged=False, binary=False):
        container = await self._get(id)
        result = await asyncio.to_thread(
            container.exec_run,
            command, stdin=interactive, tty=tty, privileged=privileged,
        )
        output = result.output
        if not binary:
            output = output.decode(errors='ignore')
        return dict(exit_code=result.exit_code, output=output)

    async def logs(self, id: str, since=None, until=None):
        container = await self._get(id)
        logs_data = await asyncio.to_thread(
            container.logs, since=parse_ts(since), until=parse_ts(until),
        )
        return logs_data.decode(errors='ignore')

    async def open_log_stream(self, id: str, since=None, until=None, follow=False):
        """Return a sync generator of log chunks; consumed on a worker thread."""
        container = await self._get(id)
        return await asyncio.to_thread(
            container.logs, stream=True, follow=follow,
            since=parse_ts(since), until=parse_ts(until),
        )

    async def get_status(self, id: str):
        return (await self._get(id)).status

    async def exec_create_tty(self, id: str, cmd) -> str:
        result = await asyncio.to_thread(
            self._api.exec_create, id, cmd, tty=True, stdin=True,
        )
        return result['Id']

    async def exec_start_socket(self, exec_id: str):
        """Start an exec and return the raw socket (SocketIO: read/write/close)."""
        return await asyncio.to_thread(
            self._api.exec_start, exec_id, socket=True, tty=True, demux=False,
        )

    async def exec_resize(self, exec_id: str, rows: int, cols: int):
        await asyncio.to_thread(
            self._api.exec_resize, exec_id, height=rows, width=cols,
        )

    async def diff(self, id: str):
        result = dict(add=[], change=[], delete=[], other=[])
        ds = {0: result['change'], 1: result['add'], 2: result['delete']}
        diff = await asyncio.to_thread((await self._get(id)).diff)
        if diff is not None:
            for i in diff:
                ds.get(i['Kind'], result['other']).append(i['Path'])
        return result

    async def commit(self, id: str, name, tag, message=None, author=None):
        from .image import ImageService

        container = await self._get(id)
        image = await asyncio.to_thread(
            container.commit, name, tag, message=message, author=author,
        )
        return ImageService.convert(image, verbose=True)
