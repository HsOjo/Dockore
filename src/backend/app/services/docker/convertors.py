import re
from datetime import datetime
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


class ContainerConvertor:
    @staticmethod
    def from_docker(obj, verbose=False):
        attrs = obj.attrs
        item = dict(
            id=obj.short_id,
            name=obj.name,
            image=ImageConvertor.from_docker(obj.image),
            create_time=attrs.get('Created', ''),
            status=obj.status,
        )
        if verbose:
            ns = attrs.get('NetworkSettings') or {}
            cfg = attrs.get('Config') or {}
            host_cfg = attrs.get('HostConfig') or {}
            # Docker API >= 1.44 移除了顶层 IPAddress/Gateway 等字段,
            # 网络信息只保留在 Networks.<name> 中, 取第一个网络并回退顶层字段
            networks = ns.get('Networks') or {}
            first = next(iter(networks.values()), {}) if networks else {}
            if cfg.get('Cmd'):
                item.update(command=' '.join(cfg['Cmd']))

            item.update(
                tty=cfg.get('Tty'),
                interactive=cfg.get('OpenStdin'),
                network=dict(
                    ip=first.get('IPAddress') or ns.get('IPAddress'),
                    prefix=(
                        first.get('IPPrefixLen')
                        if first.get('IPPrefixLen') is not None
                        else ns.get('IPPrefixLen')
                    ),
                    gateway=first.get('Gateway') or ns.get('Gateway'),
                    mac_address=first.get('MacAddress') or ns.get('MacAddress'),
                    ports=PortMappingConvertor.from_docker(host_cfg.get('PortBindings')),
                ),
                mounts=MountsConvertor.from_docker(attrs.get('Mounts') or []),
            )
        return item


class ImageConvertor:
    @staticmethod
    def from_docker(obj, verbose=False):
        attrs = obj.attrs
        item = dict(
            id=obj.short_id[7:],
            tags=obj.tags,
            author=attrs.get('Author', ''),
            create_time=attrs.get('Created', ''),
            size=attrs.get('Size', 0),
        )
        if verbose:
            cfg = attrs.get('Config') or {}
            if cfg.get('Cmd'):
                item.update(command=' '.join(cfg['Cmd']))

            item.update(
                tty=cfg.get('Tty'),
                interactive=cfg.get('OpenStdin'),
                architecture=attrs.get('Architecture'),
                os=attrs.get('Os'),
                ports=PortsConvertor.from_docker(cfg.get('ExposedPorts')),
            )
        return item


class NetworkConvertor:
    @staticmethod
    def from_docker(obj, verbose=False):
        attrs = obj.attrs
        containers = obj.containers
        item = dict(
            id=obj.short_id,
            name=obj.name,
            driver=attrs.get('Driver'),
            scope=attrs.get('Scope'),
            create_time=attrs.get('Created', ''),
            container_num=len(containers),
        )
        if verbose:
            ipam = attrs.get('IPAM') or {}
            ipam_cfg = ipam.get('Config') or []
            if ipam_cfg:
                ipam_cfg = ipam_cfg[0]
                item.update(
                    subnet=ipam_cfg.get('Subnet'),
                    gateway=ipam_cfg.get('Gateway'),
                    ip_range=ipam_cfg.get('IPRange'),
                )

            item.update(
                ipam_driver=ipam.get('Driver'),
                internal=attrs.get('Internal'),
                attachable=attrs.get('Attachable'),
                options=attrs.get('Options') or {},
                containers=[ContainerConvertor.from_docker(i, True) for i in containers],
            )
        return item


class VolumeConvertor:
    @staticmethod
    def from_docker(obj, verbose=False):
        attrs = obj.attrs
        item = dict(
            id=obj.id,
            name=obj.name,
            driver=attrs.get('Driver'),
            mount_point=attrs.get('Mountpoint'),
            scope=attrs.get('Scope'),
            create_time=attrs.get('CreatedAt', ''),
        )
        if verbose:
            item.update(driver_opts=attrs.get('Options') or {})
        return item


class HistoriesConvertor:
    @staticmethod
    def from_docker(histories: List[Dict]):
        result = []
        if histories:
            for history in histories:
                item = {k.lower(): v for k, v in history.items()}
                if 'sha256:' in item['id']:
                    item['id'] = item['id'][7:17]
                item['created_by'] = item.pop('createdby')
                item['created_time'] = datetime.fromtimestamp(
                    item.pop('created')).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                result.append(item)
        return result


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
    def to_docker(ports: list):
        if ports is None:
            return None

        result = {}
        for port in ports:
            key = '%(port)d/%(protocol)s' % port
            if key not in result:
                result[key] = (port['listen_ip'], port['listen_port'])
            else:
                if isinstance(result[key], tuple):
                    result[key] = [result[key][1], port['listen_port']]
                elif isinstance(result[key], list):
                    result[key].append(port['listen_port'])
        return result

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


class VolumesMappingConvertor:
    @staticmethod
    def to_docker(volumes: List[Dict]):
        result = {}
        for volume in volumes:
            volume = dict(volume)
            result[volume.pop('path')] = volume
        return result
