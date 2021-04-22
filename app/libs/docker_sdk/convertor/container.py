from .ports_mapping import PortMappingConvertor


class ContainerConvertor:
    @staticmethod
    def from_docker(obj, verbose=False):
        item = dict(
            id=obj.short_id,
            name=obj.name,
            image_id=obj.image.short_id,
            create_time=obj.attrs['Created'],
            status=obj.status,
        )
        if verbose:
            ns = obj.attrs['NetworkSettings']
            cfg = obj.attrs['Config']

            item.update(
                command=' '.join(cfg['Cmd']),
                tty=cfg['Tty'],
                interactive=cfg['OpenStdin'],
                network=dict(
                    ip=ns['IPAddress'],
                    prefix=ns['IPPrefixLen'],
                    gateway=ns['Gateway'],
                    mac_address=ns['MacAddress'],
                    ports=PortMappingConvertor.from_docker(obj.attrs['HostConfig']['PortBindings']),
                )
            )
        return item
