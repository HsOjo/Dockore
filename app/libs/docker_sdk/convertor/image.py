from docker.models.images import Image

from .ports import PortsConvertor


class ImageConvertor:
    @staticmethod
    def from_docker(obj: Image, verbose=False):
        attrs = obj.attrs
        item = dict(
            id=obj.short_id[7:],
            tags=obj.tags,
            author=attrs['Author'],
            create_time=attrs['Created'],
            size=attrs['Size'],
        )
        if verbose:
            cfg = attrs['Config']
            if cfg['Cmd']:
                item.update(command=' '.join(cfg['Cmd']), )

            item.update(
                tty=cfg['Tty'],
                interactive=cfg['OpenStdin'],
                architecture=attrs['Architecture'],
                os=attrs['Os'],
                ports=PortsConvertor.from_docker(cfg.get('ExposedPorts'))
            )
        return item
