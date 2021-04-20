from docker import DockerClient
from docker.models.containers import ContainerCollection, Container
from docker.models.images import ImageCollection
from docker.models.resource import Collection

from saika import Config


class CollectionAdapter:
    def __init__(self, c: Collection):
        self._c = c

    def item(self, id):
        item = self._c.get(id)
        item = self._convert(item, verbose=True)
        return item

    def list(self, verbose=False, **kwargs):
        items = self._c.list(**kwargs)
        items = [self._convert(i, verbose) for i in items]
        return items

    def _convert(self, obj, verbose=False):
        pass


class ImageAdapter(CollectionAdapter):
    _c: ImageCollection

    def _convert(self, obj, verbose=False):
        item = dict(
            id=obj.short_id,
            tags=obj.tags,
            author=obj.attrs['Author'],
            create_time=obj.attrs['Created'],
            size=obj.attrs['Size'],
        )
        if verbose:
            item.update(
                command=' '.join(obj.attrs['Config']['Cmd']),
            )
        return item

    def search(self, keyword):
        return self._c.search(keyword)

    def remove(self, id):
        self._c.remove(id)

    def pull(self, name, tag):
        item = self._c.pull(name, tag)
        return self._convert(item, True)


class ContainerAdapter(CollectionAdapter):
    _c: ContainerCollection

    def _convert(self, obj, verbose=False):
        item = dict(
            id=obj.short_id,
            name=obj.name,
            image_id=obj.image.short_id,
            create_time=obj.attrs['Created'],
            status=obj.status,
        )
        if verbose:
            item.update(
                command=' '.join(obj.attrs['Config']['Cmd'])
            )
        return item

    def remove(self, id):
        item = self._c.get(id)  # type: Container
        item.remove()

    def create(self, name, image, command):
        item = self._c.create(image, command, name=name)
        return self._convert(item, verbose=True)

    def start(self, id):
        item = self._c.get(id)  # type: Container
        item.start()

    def stop(self, id):
        item = self._c.get(id)  # type: Container
        item.stop()

    def restart(self, id):
        item = self._c.get(id)  # type: Container
        item.restart()


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
