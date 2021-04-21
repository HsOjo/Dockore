from docker.models.containers import ContainerCollection, Container, ExecResult

from .collection import CollectionAdapter
from ..util.port_mapping import PortMapping


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
                    ports=PortMapping.from_docker_py(obj.attrs['HostConfig']['PortBindings']),
                )
            )
        return item

    def remove(self, id):
        self._item(id).remove()

    def create(self, name, image, command, interactive=False, tty=False, ports=None):
        item = self._c.create(
            image, command, name=name, stdin_open=interactive, tty=tty,
            ports=PortMapping.to_docker_py(ports)
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
        diff = self._item(id).diff()
        if diff is not None:
            for i in diff:
                ds.get(i['Kind'], result['other']).append(i['Path'])

        return result
