from .ports import PortsConvertor


class ImageConvertor:
    @staticmethod
    def from_docker(obj, verbose=False):
        item = dict(
            id=obj.short_id,
            tags=obj.tags,
            author=obj.attrs['Author'],
            create_time=obj.attrs['Created'],
            size=obj.attrs['Size'],
        )
        if verbose:
            cfg = obj.attrs['Config']
            item.update(
                command=' '.join(cfg['Cmd']),
                tty=cfg['Tty'],
                interactive=cfg['OpenStdin'],
                architecture=obj.attrs['Architecture'],
                os=obj.attrs['Os'],
                ports=PortsConvertor.from_docker(cfg['ExposedPorts'])
            )
        return item
