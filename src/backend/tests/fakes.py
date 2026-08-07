from types import SimpleNamespace

from docker.errors import APIError

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


class FakeContainerService:
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
