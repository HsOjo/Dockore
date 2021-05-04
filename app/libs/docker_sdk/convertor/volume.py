from docker.models.volumes import Volume


class VolumeConvertor:
    @staticmethod
    def from_docker(obj: Volume, verbose=False):
        attrs = obj.attrs
        item = dict(
            id=obj.short_id,
            name=obj.name,
            driver=attrs['Driver'],
            scope=attrs['Scope'],
            create_time=attrs['CreatedAt'],
        )
        if verbose:
            item.update(
                mount_point=attrs['Mountpoint'],
                options=attrs['Options'],
            )

        return item
