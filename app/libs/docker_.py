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
            id=obj.attrs['Id'][:12],
            name=obj.attrs['Name'][1:],
            image_id=obj.attrs['Image'][7:19],
            create_time=obj.attrs['Created'],
            status=obj.attrs['State']['Status'],
        )
        if verbose:
            item.update(
                command=' '.join(obj.attrs['Config']['Cmd'])
            )
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
    def __init__(self, url=None):
        if url is None:
            url = Config.section('docker').get('url')
        self._cli = DockerClient(url)
        self.image = ImageAdapter(self._cli.images)
        self.container = ContainerAdapter(self._cli.containers)


if __name__ == '__main__':
    d = Docker('tcp://127.0.0.1:2375')
    print(d.image.list())
    print(d.container.list())
