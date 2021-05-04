from docker.models.containers import Container

from .image import ImageConvertor
from .ports_mapping import PortMappingConvertor


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
                    ports=PortMappingConvertor.from_docker(attrs['HostConfig']['PortBindings']),
                )
            )
        return item
