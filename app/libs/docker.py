from docker import DockerClient
from docker.models.containers import ContainerCollection, Container
from docker.models.images import ImageCollection
from docker.models.resource import Collection

from saika import Config


class CollectionAdapter:
    def __init__(self, c: Collection):
        self._c = c

    def item(self, id, raw=False):
        item = self._c.get(id)
        if not raw:
            item = self._convert(item, verbose=True)
        return item

    def list(self, verbose=False, raw=False, **kwargs):
        items = self._c.list(**kwargs)
        if not raw:
            items = [self._convert(i, verbose) for i in items]
        return items

    def _convert(self, obj, verbose=False):
        pass


class ImageAdapter(CollectionAdapter):
    _c: ImageCollection

    def _convert(self, obj, verbose=False):
        item = dict(
            id=obj.attrs['Id'],
            tags=obj.attrs['RepoTags'],
            author=obj.attrs['Author'],
            create_time=obj.attrs['Created'],
            size=obj.attrs['Size'],
        )
        if verbose:
            item.update(
                command=' '.join(obj.attrs['Config']['Cmd']),
            )
        return item

    def remove(self, id):
        self._c.remove(id)


class ContainerAdapter(CollectionAdapter):
    _c: ContainerCollection

    def _convert(self, obj, verbose=False):
        item = dict(
            id=obj.attrs['Id'],
            name=obj.attrs['Name'],
            image_id=obj.attrs['Image'],
            create_time=obj.attrs['Created'],
        )
        if verbose:
            pass
        return item

    def remove(self, id):
        item = self.item(id, raw=True)  # type: Container
        item.remove()

    def create(self, name, image, command, raw=False):
        item = self._c.create(image, command, name=name)
        if not raw:
            self._convert(item, verbose=True)
        return item


class Docker:
    def __init__(self):
        self._cli = DockerClient(Config.section('docker').get('url'))
        self.image = ImageAdapter(self._cli.images)
        self.container = ContainerAdapter(self._cli.containers)
