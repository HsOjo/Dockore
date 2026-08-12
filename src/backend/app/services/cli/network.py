from typing import Optional

from app.core.validators import validate_docker_name, validate_no_dash
from .convertors import OptionConvertor
from .docker_cli import DockerCli
from .errors import DockerNotFound


def _endpoint_to_container(container_id: str, endpoint: dict, gateway: Optional[str]) -> dict:
    address = endpoint.get('IPv4Address') or endpoint.get('IPv6Address') or ''
    ip, _, prefix = address.partition('/')
    return dict(
        id=container_id[:12],
        name=endpoint.get('Name') or '',
        image=dict(id='', tags=[], create_time=''),
        create_time='',
        status='',
        network=dict(
            ip=ip or None,
            prefix=int(prefix) if prefix else None,
            gateway=gateway,
        ),
    )


def network_item_from_inspect(attrs: dict, verbose: bool = False) -> dict:
    containers = attrs.get('Containers') or {}
    item = dict(
        id=(attrs.get('Id') or '')[:12],
        name=attrs.get('Name'),
        driver=attrs.get('Driver'),
        scope=attrs.get('Scope'),
        create_time=attrs.get('Created') or '',
        container_num=len(containers),
    )
    if verbose:
        ipam = attrs.get('IPAM') or {}
        ipam_cfg = ipam.get('Config') or []
        gateway = None
        if ipam_cfg:
            gateway = ipam_cfg[0].get('Gateway')
            item.update(
                subnet=ipam_cfg[0].get('Subnet'),
                gateway=gateway,
                ip_range=ipam_cfg[0].get('IPRange'),
            )
        item.update(
            ipam_driver=ipam.get('Driver'),
            internal=attrs.get('Internal'),
            attachable=attrs.get('Attachable'),
            options=attrs.get('Options') or {},
            containers=[
                _endpoint_to_container(cid, ep, gateway)
                for cid, ep in containers.items()
            ],
        )
    return item


class NetworkService:

    def __init__(self, cli: DockerCli):
        self._cli = cli

    async def list(self, verbose: bool = False, **kwargs):
        rows = await self._cli.run_json_lines(
            'network', 'ls', '--no-trunc', '--format', '{{json .}}',
        )
        ids = [row['ID'] for row in rows if row.get('ID')]
        if not ids:
            return []
        inspects = await self._cli.inspect_list(*ids)
        return [network_item_from_inspect(a, verbose) for a in inspects]

    async def item(self, id: str):
        try:
            attrs = await self._cli.inspect(id)
        except DockerNotFound:
            return None
        return network_item_from_inspect(attrs, verbose=True)

    async def remove(self, id: str):
        await self._cli.run('network', 'rm', id)

    async def create(self, name, driver, attachable=True, options=None,
                     subnet=None, gateway=None, ip_range=None):
        name = validate_docker_name(name, "network name")
        if driver:
            driver = validate_no_dash(driver, "driver")
        if subnet:
            subnet = validate_no_dash(subnet, "subnet")
        if gateway:
            gateway = validate_no_dash(gateway, "gateway")
        if ip_range:
            ip_range = validate_no_dash(ip_range, "ip_range")
        args = ['network', 'create']
        if driver:
            args += ['--driver', driver]
        if subnet:
            args += ['--subnet', subnet]
        if gateway:
            args += ['--gateway', gateway]
        if ip_range:
            args += ['--ip-range', ip_range]
        if attachable:
            args.append('--attachable')
        for k, v in OptionConvertor.to(options or []).items():
            args += ['--opt', f'{k}={v}']
        args.append(name)
        await self._cli.run(*args)
        return await self.item(name)

    async def connect(self, id: str, container_id: str, ipv4_address: Optional[str] = None):
        args = ['network', 'connect']
        if ipv4_address:
            ipv4_address = validate_no_dash(ipv4_address, "ipv4_address")
            args += ['--ip', ipv4_address]
        args += [id, container_id]
        await self._cli.run(*args)

    async def disconnect(self, id: str, container_id: str, force: bool = False):
        args = ['network', 'disconnect']
        if force:
            args.append('--force')
        args += [id, container_id]
        await self._cli.run(*args)
