import re
from typing import Dict, List


def dict_to_lower(obj):
    if isinstance(obj, dict):
        r = {}
        for k, v in obj.items():
            k = re.sub('[A-Z]+', lambda x: '_%s' % x.group().lower(), k).lstrip('_')
            r[k] = dict_to_lower(v)
        return r
    elif isinstance(obj, list):
        return [dict_to_lower(i) for i in obj]
    return obj


def remove_empty_obj(obj):
    if isinstance(obj, list):
        r = []
        for i in obj:
            i = remove_empty_obj(i)
            if i or i is False:
                r.append(i)
        return r
    elif isinstance(obj, dict):
        r = {}
        for k, v in obj.items():
            v = remove_empty_obj(v)
            if v or v is False:
                r[k] = v
        return r
    return obj


class OptionConvertor:
    @staticmethod
    def to(obj: List[Dict]):
        result = {}
        for i in obj:
            result[i['key']] = i['value']
        return result


class PortsConvertor:
    @staticmethod
    def from_docker(ports: dict):
        result = []
        if ports:
            for k in ports:
                port, protocol = k.split('/')
                result.append(dict(port=int(port), protocol=protocol))
        return result


class PortMappingConvertor:
    @staticmethod
    def from_docker(ports: dict):
        if ports is None:
            return None

        result = []
        for inner, host in ports.items():
            host: List[Dict]
            port, protocol = inner.split('/')
            for i in host:
                result.append(dict(
                    port=int(port), protocol=protocol,
                    listen_ip=i['HostIp'], listen_port=int(i['HostPort']),
                ))
        return result

    @staticmethod
    def to_cli_args(ports: list) -> list[str]:
        """[`-p`, `listen_ip:listen_port:port/protocol`, ...] for docker create/run."""
        args: list[str] = []
        for port in ports or []:
            listen_ip = port.get('listen_ip') or ''
            listen_port = port.get('listen_port')
            spec = f"{port['port']}/{port.get('protocol', 'tcp')}"
            spec = f"{listen_port}:{spec}" if listen_port is not None else spec
            if listen_ip:
                spec = f"{listen_ip}:{spec}"
            args += ['-p', spec]
        return args


class VolumesMappingConvertor:
    @staticmethod
    def to_cli_args(volumes: List[Dict]) -> list[str]:
        """[`-v`, `bind:path[:mode]`, ...] for docker create/run."""
        args: list[str] = []
        for volume in volumes or []:
            spec = f"{volume['bind']}:{volume['path']}"
            if volume.get('mode'):
                spec += f":{volume['mode']}"
            args += ['-v', spec]
        return args


class MountsConvertor:
    @staticmethod
    def from_docker(mounts: List[dict]):
        result = []
        for mount in mounts:
            result.append(dict(
                name=mount.get('Name'), type=mount.get('Type'), driver=mount.get('Driver'),
                mode=mount.get('Mode'), src=mount.get('Source'), dest=mount.get('Destination'),
            ))
        return result
