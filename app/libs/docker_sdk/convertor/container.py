from docker.models.containers import Container

from .image import ImageConvertor
from .ports_mapping import PortMappingConvertor
from .volumes_mapping import VolumesMappingConvertor
from .mounts import MountsConvertor


class ContainerConvertor:
    @staticmethod
    def from_docker(obj: Container, verbose=False):
        attrs = obj.attrs
        item = dict(
            id=obj.short_id,
            name=obj.name,
            image=ImageConvertor.from_docker(obj.image),
            create_time=attrs['Created'],
            status=obj.status,
        )
        if verbose:
            ns = attrs['NetworkSettings']
            cfg = attrs['Config']
            host_cfg = attrs['HostConfig']
            if cfg['Cmd']:
                item.update(command=' '.join(cfg['Cmd']), )

            item.update(
                tty=cfg['Tty'],
                interactive=cfg['OpenStdin'],
                network=dict(
                    ip=ns['IPAddress'],
                    prefix=ns['IPPrefixLen'],
                    gateway=ns['Gateway'],
                    mac_address=ns['MacAddress'],
                    ports=PortMappingConvertor.from_docker(host_cfg['PortBindings']),
                ),
                mounts=MountsConvertor.from_docker(attrs['Mounts']),
            )
        return item
