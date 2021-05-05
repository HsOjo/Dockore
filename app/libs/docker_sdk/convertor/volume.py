from docker.models.volumes import Volume


class VolumeConvertor:
    @staticmethod
    def from_docker(obj: Volume, verbose=False):
        attrs = obj.attrs
        item = dict(
            id=obj.id,
            name=obj.name,
            driver=attrs['Driver'],
            mount_point=attrs['Mountpoint'],
            scope=attrs['Scope'],
            create_time=attrs['CreatedAt'],
        )
        if verbose:
            item.update(
                driver_opts=attrs['Options'],
            )

        return item
