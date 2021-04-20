from docker import DockerClient
from docker.models.containers import ContainerCollection, Container
from docker.models.images import ImageCollection, Image
from docker.models.resource import Collection


class CollectionAdapter:
    def __init__(self, c: Collection):
        self._c = c

    def item(self, id):
        item = self._item(id)
        item = self._convert(item, verbose=True)
        return item

    def list(self, verbose=False, **kwargs):
        items = self._c.list(**kwargs)
        items = [self._convert(i, verbose) for i in items]
        return items

    def _convert(self, obj, verbose=False):
        pass

    def _item(self, id):
        pass


class ImageAdapter(CollectionAdapter):
    _c: ImageCollection

    def _item(self, id):
        item = self._c.get(id)  # type: Image
        return item

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
                tty=obj.attrs['Config']['Tty'],
                interactive=obj.attrs['Config']['OpenStdin'],
                architecture=obj.attrs['Architecture'],
                os=obj.attrs['Os'],
            )
        return item

    def search(self, keyword):
        return self._c.search(keyword)

    def remove(self, id):
        self._c.remove(id)

    def pull(self, name, tag):
        if not tag:
            tag = 'latest'
        if tag == '*':
            tag = None
        item = self._c.pull(name, tag)
        return self._convert(item, True)


class ContainerAdapter(CollectionAdapter):
    _c: ContainerCollection

    def _item(self, id):
        item = self._c.get(id)  # type: Container
        return item

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
                command=' '.join(obj.attrs['Config']['Cmd']),
                tty=obj.attrs['Config']['Tty'],
                interactive=obj.attrs['Config']['OpenStdin'],
                network=dict(
                    ip=obj.attrs['NetworkSettings']['IPAddress'],
                    prefix=obj.attrs['NetworkSettings']['IPPrefixLen'],
                    gateway=obj.attrs['NetworkSettings']['Gateway'],
                    mac_address=obj.attrs['NetworkSettings']['MacAddress'],
                    ports=obj.attrs['NetworkSettings']['Ports'],
                )
            )
        return item

    def remove(self, id):
        self._item(id).remove()

    def create(self, name, image, command, interactive=False, tty=False):
        item = self._c.create(
            image, command, name=name, stdin_open=interactive, tty=tty,
        )
        return self._convert(item, verbose=True)

    def start(self, id):
        self._item(id).start()

    def stop(self, id, timeout=None):
        self._item(id).stop(timeout=timeout)

    def restart(self, id, timeout=None):
        self._item(id).restart(timeout=timeout)


class Docker:
    def __init__(self, url):
        self._cli = DockerClient(url)
        self.image = ImageAdapter(self._cli.images)
        self.container = ContainerAdapter(self._cli.containers)


if __name__ == '__main__':
    d = Docker('tcp://127.0.0.1:2375')
    print(d.image.list())
    print(d.container.list())
