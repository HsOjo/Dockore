from typing import Optional

from app.core.validators import validate_docker_name, validate_no_dash
from .convertors import OptionConvertor
from .docker_cli import DockerCli
from .errors import DockerNotFound


def volume_item_from_inspect(attrs: dict, verbose: bool = False) -> dict:
    name = attrs.get('Name') or ''
    item = dict(
        id=name,
        name=name,
        driver=attrs.get('Driver'),
        mount_point=attrs.get('Mountpoint'),
        scope=attrs.get('Scope'),
        create_time=attrs.get('CreatedAt') or '',
    )
    if verbose:
        item.update(driver_opts=attrs.get('Options') or {})
    return item


class VolumeService:

    def __init__(self, cli: DockerCli):
        self._cli = cli

    async def list(self, verbose: bool = False, **kwargs):
        rows = await self._cli.run_json_lines('volume', 'ls', '--format', '{{json .}}')
        names = [row['Name'] for row in rows if row.get('Name')]
        if not names:
            return []
        inspects = await self._cli.inspect_list(*names)
        return [volume_item_from_inspect(a, verbose) for a in inspects]

    async def item(self, id: str):
        try:
            attrs = await self._cli.inspect(id)
        except DockerNotFound:
            return None
        return volume_item_from_inspect(attrs, verbose=True)

    async def remove(self, id: str):
        await self._cli.run('volume', 'rm', id)

    async def create(self, name, driver: Optional[str] = None, driver_opts=None):
        name = validate_docker_name(name, "volume name")
        if driver:
            driver = validate_no_dash(driver, "driver")
        args = ['volume', 'create']
        if driver:
            args += ['--driver', driver]
        for k, v in OptionConvertor.to(driver_opts or []).items():
            args += ['--opt', f'{k}={v}']
        args += ['--name', name]
        await self._cli.run(*args)
        return await self.item(name)
