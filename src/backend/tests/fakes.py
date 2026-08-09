from collections import deque
import threading
from types import SimpleNamespace

from docker.errors import APIError, NotFound

from app.services.docker.convertors import (
    ContainerConvertor,
    ImageConvertor,
    NetworkConvertor,
    VolumeConvertor,
)


def make_image_obj():
    return SimpleNamespace(
        short_id="sha256:0123456789ab",
        tags=["nginx:latest"],
        attrs={
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
        },
    )


def make_container_obj():
    return SimpleNamespace(
        short_id="abcdef1234",
        name="web",
        image=make_image_obj(),
        status="running",
        attrs={
            "Created": "2024-01-01T00:00:00.000000000Z",
            "Config": {"Cmd": ["nginx"], "Tty": True, "OpenStdin": True},
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
        },
    )


def make_network_obj(containers=None):
    return SimpleNamespace(
        short_id="net1234abc",
        name="bridge",
        containers=containers or [],
        attrs={
            "Driver": "bridge",
            "Scope": "local",
            "Created": "2024-01-01T00:00:00.000000000Z",
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
        },
    )


def make_volume_obj():
    return SimpleNamespace(
        id="vol1234",
        name="data",
        attrs={
            "Driver": "local",
            "Mountpoint": "/var/lib/docker/volumes/data/_data",
            "Scope": "local",
            "CreatedAt": "2024-01-01T00:00:00Z",
            "Options": {},
        },
    )


CONTAINER = ContainerConvertor.from_docker(make_container_obj(), verbose=True)
IMAGE = ImageConvertor.from_docker(make_image_obj(), verbose=True)
NETWORK = NetworkConvertor.from_docker(make_network_obj(), verbose=True)
VOLUME = VolumeConvertor.from_docker(make_volume_obj(), verbose=True)


class FakeSocket:
    """SocketIO-like fake (read/write/close) with thread-safe blocking read."""

    def __init__(self, chunks=None):
        self._chunks = deque(chunks or [])
        self.written = []
        self.closed = False
        self._cv = threading.Condition()

    def feed(self, data: bytes):
        with self._cv:
            self._chunks.append(data)
            self._cv.notify_all()

    def read(self, n: int = 4096) -> bytes:
        with self._cv:
            while not self._chunks and not self.closed:
                self._cv.wait(timeout=5)
            if self._chunks:
                return self._chunks.popleft()
            return b""

    def write(self, data: bytes) -> int:
        self.written.append(data)
        return len(data)

    def close(self):
        with self._cv:
            self.closed = True
            self._cv.notify_all()


class FakeContainerService:
    def __init__(self):
        self.terminal_socket = FakeSocket()
        self.exec_created = []
        self.resized = []
        self.log_stream_calls = []

    async def list(self, all=False, verbose=False):
        return [CONTAINER]

    async def item(self, id):
        return CONTAINER if id == CONTAINER["id"] else None

    async def remove(self, id):
        if id == "bad":
            raise APIError(f"cannot remove {id}")

    async def create(self, **kwargs):
        return CONTAINER

    async def run(self, **kwargs):
        return CONTAINER

    async def start(self, id):
        pass

    async def stop(self, id, timeout=None):
        pass

    async def restart(self, id, timeout=None):
        pass

    async def rename(self, id, name):
        pass

    async def exec(self, id, command, **kwargs):
        return {"exit_code": 0, "output": "ok\n"}

    async def logs(self, id, since=None, until=None):
        return "log line\n"

    async def diff(self, id):
        return {"add": ["/new"], "change": ["/etc"], "delete": [], "other": []}

    async def commit(self, id, name, tag, message=None, author=None):
        return IMAGE

    async def get_status(self, id):
        if id != CONTAINER["id"]:
            raise NotFound(f"no such container: {id}")
        return "running"

    async def exec_create_tty(self, id, cmd):
        self.exec_created.append((id, cmd))
        return "exec123"

    async def exec_start_socket(self, exec_id):
        return self.terminal_socket

    async def exec_resize(self, exec_id, rows, cols):
        self.resized.append((exec_id, rows, cols))

    async def open_log_stream(self, id, since=None, until=None, follow=False):
        if id != CONTAINER["id"]:
            raise NotFound(f"no such container: {id}")
        self.log_stream_calls.append(dict(since=since, until=until, follow=follow))
        return iter([b"log line 1\n", b"log line 2\n"])


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
            raise APIError(f"cannot remove {id}")

    def pull_stream(self, name, tag):
        return iter([
            {"status": "Pulling from library/nginx", "id": None, "progress": None},
            {"status": "Download complete", "id": "abc", "progress": "100%"},
        ])

    async def tag(self, id, name, tag):
        return True

    async def history(self, id):
        return [
            {
                "id": "0123456789",
                "created_by": "/bin/sh -c #(nop) CMD",
                "created_time": "2024-01-01T00:00:00.000000Z",
                "size": 0,
                "tags": None,
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
            raise APIError(f"cannot remove {id}")

    async def create(self, **kwargs):
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
            raise APIError(f"cannot remove {id}")

    async def create(self, **kwargs):
        return VOLUME


class FakeDocker:
    def __init__(self):
        self.container = FakeContainerService()
        self.image = FakeImageService()
        self.network = FakeNetworkService()
        self.volume = FakeVolumeService()

    async def version(self):
        return {"engine": {"version": "24.0.0", "api_version": "1.43"}}
