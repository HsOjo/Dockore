from docker.models.networks import Network

from .container import ContainerConvertor


class NetworkConvertor:
    @staticmethod
    def from_docker(obj: Network, verbose=False):
        attrs = obj.attrs
        containers = obj.containers
        item = dict(
            id=obj.short_id,
            name=obj.name,
            driver=attrs['Driver'],
            scope=attrs['Scope'],
            create_time=attrs['Created'],
            container_num=len(containers)
        )
        if verbose:
            ipam = attrs['IPAM']
            ipam_cfg = ipam['Config']
            if ipam_cfg:
                ipam_cfg = ipam_cfg[0]  # type: dict
                item.update(
                    subnet=ipam_cfg.get('Subnet'),
                    gateway=ipam_cfg.get('Gateway'),
                    ip_range=ipam_cfg.get('IPRange'),
                )

            item.update(
                ipam_driver=ipam['Driver'],
                internal=attrs['Internal'],
                attachable=attrs['Attachable'],
                options=attrs['Options'],
                containers=[ContainerConvertor.from_docker(i, True) for i in containers]
            )

        return item
