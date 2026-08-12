import asyncio
import itertools

from app.services.cli.container import container_item_from_inspect
from app.services.cli.errors import DockerApiError, DockerNotFound
from app.services.cli.image import image_item_from_inspect
from app.services.cli.network import network_item_from_inspect
from app.services.cli.volume import volume_item_from_inspect


def make_image_attrs():
    return {
        "Id": "sha256:" + "0123456789ab" + "0" * 52,
        "RepoTags": ["nginx:latest"],
        "Author": "nginx",
        "Created": "2024-01-01T00:00:00.000000000Z",
        "Size": 12345,
        "Config": {
            "Cmd": ["nginx", "-g", "daemon off;"],
            "Tty": False,
            "OpenStdin": False,
            "ExposedPorts": {"80/tcp": {}},
        },
        "Architecture": "amd64",
        "Os": "linux",
    }


def make_container_attrs():
    return {
        "Id": "abcdef123456" + "0" * 52,
        "Name": "/web",
        "Created": "2024-01-01T00:00:00.000000000Z",
        "Image": "sha256:" + "0123456789ab" + "0" * 52,
        "State": {"Status": "running"},
        "Config": {
            "Cmd": ["nginx"],
            "Tty": True,
            "OpenStdin": True,
            "Image": "nginx:latest",
        },
        "NetworkSettings": {
            "IPAddress": "172.17.0.2",
            "IPPrefixLen": 16,
            "Gateway": "172.17.0.1",
            "MacAddress": "02:42:ac:11:00:02",
        },
        "HostConfig": {
            "PortBindings": {
                "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}],
            },
        },
        "Mounts": [
            {
                "Name": "data",
                "Type": "volume",
                "Driver": "local",
                "Mode": "rw",
                "Source": "/var/lib/docker/volumes/data/_data",
                "Destination": "/data",
            },
        ],
    }


def make_network_attrs(containers=None):
    return {
        "Id": "net1234abcdef" + "0" * 52,
        "Name": "bridge",
        "Driver": "bridge",
        "Scope": "local",
        "Created": "2024-01-01T00:00:00.000000000Z",
        "Containers": containers or {},
        "IPAM": {
            "Driver": "default",
            "Config": [
                {
                    "Subnet": "172.17.0.0/16",
                    "Gateway": "172.17.0.1",
                    "IPRange": None,
                },
            ],
        },
        "Internal": False,
        "Attachable": True,
        "Options": {},
    }


def make_volume_attrs():
    return {
        "Name": "data",
        "Driver": "local",
        "Mountpoint": "/var/lib/docker/volumes/data/_data",
        "Scope": "local",
        "CreatedAt": "2024-01-01T00:00:00Z",
        "Options": {},
    }


IMAGE = image_item_from_inspect(make_image_attrs(), verbose=True)
CONTAINER = container_item_from_inspect(make_container_attrs(), IMAGE, verbose=True)
NETWORK = network_item_from_inspect(make_network_attrs(), verbose=True)
VOLUME = volume_item_from_inspect(make_volume_attrs(), verbose=True)


class FakeCliTask:
    """CliTask stand-in: records stdin/winsize, exposes callbacks for feeding."""

    def __init__(self, id, kind, stack, args):
        self.id = id
        self.kind = kind
        self.stack = stack
        self.args = args
        self.status = "running"
        self.returncode = None
        self.error = None
        self.written = []
        self.resizes = []
        self.on_data = None
        self.on_done = None

    def write(self, data: bytes) -> None:
        self.written.append(data)

    def resize(self, rows: int, cols: int) -> None:
        self.resizes.append((rows, cols))


class FakeExecutor:
    """CliExecutor stand-in: stream() captures callbacks; feed/finish drive them.

    feed/finish are called from the sync test thread and hop into the app loop.
    """

    _ids = itertools.count(1)

    def __init__(self):
        self.tasks = {}
        self.streams = []
        self.loop = None

    async def stream(self, kind, stack, args, on_data, cwd=None,
                     on_done=None, line_mode=False):
        task = FakeCliTask(f"fake-task-{next(self._ids)}", kind, stack, args)
        task.on_data = on_data
        task.on_done = on_done
        self.tasks[task.id] = task
        self.streams.append(dict(
            task=task, kind=kind, stack=stack, args=args,
            cwd=cwd, line_mode=line_mode,
        ))
        self.loop = asyncio.get_running_loop()
        return task

    def feed(self, task, data: bytes):
        asyncio.run_coroutine_threadsafe(
            task.on_data(task, data), self.loop,
        ).result(timeout=5)

    def finish(self, task, error=None):
        if error:
            task.status = "error"
            task.error = error
            task.returncode = -1
        else:
            task.status = "done"
            task.returncode = 0
        asyncio.run_coroutine_threadsafe(
            task.on_done(task), self.loop,
        ).result(timeout=5)

    async def cancel(self, task_id):
        task = self.tasks.get(task_id)
        if not task or task.status != "running":
            return False
        task.status = "cancelled"
        return True

    def get_task(self, task_id):
        return self.tasks.get(task_id)


class FakeCli:
    def __init__(self, docker_host=""):
        self.docker_host = docker_host
        self.executor = FakeExecutor()


class FakeContainerService:
    async def list(self, all=False, verbose=False):
        return [CONTAINER]

    async def item(self, id):
        return CONTAINER if id == CONTAINER["id"] else None

    async def remove(self, id):
        if id == "bad":
            raise DockerApiError(f"cannot remove {id}")

    async def create(self, name, image, command, interactive=False, tty=False,
                     privileged=False, ports=None, volumes=None):
        return CONTAINER

    async def run(self, name, image, command, interactive=False, tty=False,
                  privileged=False, ports=None, volumes=None):
        return CONTAINER

    async def start(self, id):
        pass

    async def stop(self, id, timeout=None):
        pass

    async def restart(self, id, timeout=None):
        pass

    async def rename(self, id, name):
        pass

    async def exec(self, id, command, interactive=False, tty=False,
                   privileged=False, binary=False):
        return {"exit_code": 0, "output": "ok\n"}

    async def logs(self, id, since=None, until=None):
        return "log line\n"

    async def diff(self, id):
        return {"add": ["/new"], "change": ["/etc"], "delete": [], "other": []}

    async def commit(self, id, name, tag, message=None, author=None):
        return IMAGE

    async def get_status(self, id):
        if id != CONTAINER["id"]:
            raise DockerNotFound(f"no such container: {id}")
        return "running"


class FakeImageService:
    async def list(self, all=False, verbose=False):
        return [IMAGE]

    async def item(self, id):
        return IMAGE if id == IMAGE["id"] else None

    async def search(self, keyword):
        return [
            {
                "name": "nginx",
                "description": "Official build of Nginx.",
                "star_count": 100,
                "is_official": True,
                "is_automated": False,
            },
        ]

    async def remove(self, id, tag_only=False):
        if id == "bad":
            raise DockerApiError(f"cannot remove {id}")

    async def tag(self, id, name, tag=None):
        return True

    async def history(self, id):
        return [
            {
                "id": "0123456789",
                "created_by": "/bin/sh -c #(nop) CMD",
                "created_time": "2024-01-01T00:00:00.000000Z",
                "size": 0,
                "comment": "",
            },
        ]


class FakeNetworkService:
    async def list(self, verbose=False, **kwargs):
        return [NETWORK]

    async def item(self, id):
        return NETWORK if id == NETWORK["id"] else None

    async def remove(self, id):
        if id == "bad":
            raise DockerApiError(f"cannot remove {id}")

    async def create(self, name, driver, attachable=True, options=None,
                     subnet=None, gateway=None, ip_range=None):
        return NETWORK

    async def connect(self, id, container_id, ipv4_address=None):
        pass

    async def disconnect(self, id, container_id, force=False):
        pass


class FakeVolumeService:
    async def list(self, verbose=False, **kwargs):
        return [VOLUME]

    async def item(self, id):
        return VOLUME if id == VOLUME["id"] else None

    async def remove(self, id):
        if id == "bad":
            raise DockerApiError(f"cannot remove {id}")

    async def create(self, name, driver=None, driver_opts=None):
        return VOLUME


class FakeDocker:
    def __init__(self, docker_host=""):
        self.cli = FakeCli(docker_host)
        self.container = FakeContainerService()
        self.image = FakeImageService()
        self.network = FakeNetworkService()
        self.volume = FakeVolumeService()

    async def version(self):
        return {"engine": {"version": "24.0.0", "api_version": "1.43"}}
