from docker.models.networks import Network


class NetworkConvertor:
    @staticmethod
    def from_docker(obj: Network, verbose=False):
        attrs = obj.attrs
        item = dict(
            id=obj.short_id,
            name=obj.name,
            driver=attrs['Driver'],
            scope=attrs['Scope'],
            create_time=attrs['Created'],
        )
        if verbose:
            ipam = attrs['IPAM']
            ipam_cfg = ipam['Config']
            if ipam_cfg:
                ipam_cfg = ipam_cfg[0]
                item.update(
                    subnet=ipam_cfg['Subnet'],
                    gateway=ipam_cfg['Gateway'],
                )

            item.update(
                ipam_driver=ipam['Driver'],
                internal=attrs['Internal'],
                attachable=attrs['Attachable'],
                options=attrs['Options'],
            )

        return item