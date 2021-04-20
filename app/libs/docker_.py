from docker import DockerClient
from docker.models.containers import ContainerCollection, Container, ExecResult
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
            cfg = obj.attrs['Config']
            item.update(
                command=' '.join(cfg['Cmd']),
                tty=cfg['Tty'],
                interactive=cfg['OpenStdin'],
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

    def tag(self, id, name, tag):
        return self._c.get(id).tag(name, tag)


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
                    ports=obj.ports,
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

    def rename(self, id, name):
        self._item(id).rename(name)

    def exec(self, id, command, interactive=False, tty=False, privileged=False):
        result = self._item(id).exec_run(
            command, stdin=interactive, tty=tty, privileged=privileged
        )  # type: ExecResult
        return dict(
            exit_code=result.exit_code,
            output=result.output.decode(errors='ignore'),
        )

    def logs(self, id, since, until):
        logs_data = self._item(id).logs(since=since, until=until)  # type: bytes
        return logs_data.decode(errors='ignore')

    def diff(self, id):
        result = dict(add=[], change=[], delete=[], other=[])
        ds = {0: result['change'], 1: result['add'], 2: result['delete']}
        for i in self._item(id).diff():
            ds.get(i['Kind'], result['other']).append(i['Path'])

        return result


class Docker:
    def __init__(self, url):
        self._cli = DockerClient(url)
        self.image = ImageAdapter(self._cli.images)
        self.container = ContainerAdapter(self._cli.containers)


if __name__ == '__main__':
    d = Docker('tcp://127.0.0.1:2375')
    print(d.image.list())
    print(d.container.list())
