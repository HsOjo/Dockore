import re
from typing import Optional

from app.core.validators import validate_docker_name, validate_image_ref, validate_no_dash
from .convertors import PortsConvertor
from .docker_cli import DockerCli
from .errors import DockerNotFound

_SIZE_UNITS = {
    '': 1,
    'B': 1,
    'KB': 10**3,
    'MB': 10**6,
    'GB': 10**9,
    'TB': 10**12,
    'KIB': 1024,
    'MIB': 1024**2,
    'GIB': 1024**3,
    'TIB': 1024**4,
}


def _parse_size(text) -> int:
    m = re.match(r'^\s*([\d.]+)\s*([A-Za-z]*)\s*$', str(text or '0'))
    if not m:
        return 0
    value, unit = m.groups()
    return int(float(value) * _SIZE_UNITS.get(unit.upper(), 1))


def _ok_flag(value) -> bool:
    if value is True:
        return True
    return str(value or '').strip('[]').lower() in ('ok', 'true')


def image_item_from_inspect(attrs: dict, verbose: bool = False) -> dict:
    tags = [t for t in (attrs.get('RepoTags') or []) if t != '<none>:<none>']
    item = dict(
        id=(attrs.get('Id') or '').replace('sha256:', '')[:12],
        tags=tags,
        author=attrs.get('Author') or '',
        create_time=attrs.get('Created') or '',
        size=attrs.get('Size') or 0,
    )
    if verbose:
        cfg = attrs.get('Config') or {}
        cmd = cfg.get('Cmd')
        if cmd:
            item.update(command=' '.join(cmd) if isinstance(cmd, list) else str(cmd))
        item.update(
            tty=cfg.get('Tty'),
            interactive=cfg.get('OpenStdin'),
            architecture=attrs.get('Architecture'),
            os=attrs.get('Os'),
            ports=PortsConvertor.from_docker(cfg.get('ExposedPorts')),
        )
    return item


class ImageService:

    def __init__(self, cli: DockerCli):
        self._cli = cli

    async def list(self, all: bool = False, verbose: bool = False):
        args = ['image', 'ls', '--no-trunc', '--format', '{{json .}}']
        if all:
            args.append('--all')
        rows = await self._cli.run_json_lines(*args)
        ids = []
        for row in rows:
            image_id = row.get('ID')
            if image_id and image_id not in ids:
                ids.append(image_id)
        if not ids:
            return []
        inspects = await self._cli.inspect_list(*ids)
        return [image_item_from_inspect(a, verbose) for a in inspects]

    async def item(self, id: str):
        try:
            attrs = await self._cli.inspect(id)
        except DockerNotFound:
            return None
        return image_item_from_inspect(attrs, verbose=True)

    async def search(self, keyword: str):
        keyword = validate_no_dash(keyword, "keyword")
        rows = await self._cli.run_json_lines('search', '--format', '{{json .}}', keyword)
        return [dict(
            name=row.get('Name'),
            description=row.get('Description'),
            star_count=int(row.get('StarCount') or 0),
            is_official=_ok_flag(row.get('IsOfficial')),
            is_automated=_ok_flag(row.get('IsAutomated')),
        ) for row in rows]

    async def remove(self, id: str, tag_only: bool = False):
        await self._cli.run('rmi', id)

    async def tag(self, id: str, name: str, tag: Optional[str] = None):
        name = validate_docker_name(name, "image name")
        if tag:
            tag = validate_no_dash(tag, "tag")
        target = f'{name}:{tag}' if tag else name
        target = validate_image_ref(target, "target")
        await self._cli.run('tag', id, target)
        return True

    async def history(self, id: str):
        rows = await self._cli.run_json_lines('history', '--format', '{{json .}}', id)
        result = []
        for row in rows:
            image_id = row.get('ID') or ''
            if image_id.startswith('sha256:'):
                image_id = image_id[7:17]
            result.append(dict(
                id=image_id,
                created_by=row.get('CreatedBy') or '',
                created_time=row.get('CreatedAt') or '',
                size=_parse_size(row.get('Size')),
                comment=row.get('Comment') or '',
            ))
        return result
