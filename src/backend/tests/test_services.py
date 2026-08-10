from types import SimpleNamespace

import pytest
from docker.errors import NotFound

from app.services.docker.client import Docker
from app.services.docker.container import ContainerService, parse_ts
from app.services.docker.image import ImageService
from app.services.docker.network import NetworkService
from app.services.docker.volume import VolumeService
from tests.fakes import (
    make_container_obj,
    make_image_obj,
    make_network_obj,
    make_volume_obj,
)


def test_parse_ts():
    assert parse_ts(None) is None
    assert parse_ts(123) == 123
    assert parse_ts("123") == 123
    assert parse_ts("2024-01-01T00:00:00").year == 2024


class FakeContainerObj:
    def __init__(self):
        self._base = make_container_obj()
        self.calls = []

    def __getattr__(self, name):
        return getattr(self._base, name)

    def remove(self):
        self.calls.append("remove")

    def start(self):
        self.calls.append("start")

    def stop(self, timeout=None):
        self.calls.append(("stop", timeout))

    def restart(self, timeout=None):
        self.calls.append(("restart", timeout))

    def rename(self, name):
        self.calls.append(("rename", name))

    def exec_run(self, command, **kwargs):
        self.calls.append(("exec_run", command, kwargs))
        return SimpleNamespace(exit_code=0, output=b"total 0\n")

    def logs(self, **kwargs):
        self.calls.append(("logs", kwargs))
        if kwargs.get("stream"):
            return iter([b"a\n", b"b\n"])
        return b"log text\n"

    def diff(self):
        self.calls.append("diff")
        return [
            {"Kind": 0, "Path": "/etc/passwd"},
            {"Kind": 1, "Path": "/new"},
            {"Kind": 2, "Path": "/gone"},
            {"Kind": 9, "Path": "/weird"},
        ]

    def commit(self, name, tag, **kwargs):
        self.calls.append(("commit", name, tag, kwargs))
        return make_image_obj()


class FakeContainersCollection:
    def __init__(self):
        self.obj = FakeContainerObj()
        self.create_kwargs = None
        self.run_kwargs = None

    def list(self, all=False):
        self.list_all = all
        return [self.obj]

    def get(self, id):
        if id == "missing":
            raise NotFound("no such container")
        return self.obj

    def create(self, *args, **kwargs):
        self.create_kwargs = (args, kwargs)
        return self.obj

    def run(self, *args, **kwargs):
        self.run_kwargs = (args, kwargs)
        return self.obj


class FakeLowLevelAPI:
    def __init__(self):
        self.exec_calls = []
        self.pull_calls = []

    def exec_create(self, id, cmd, **kwargs):
        self.exec_calls.append(("create", id, cmd, kwargs))
        return {"Id": "exec-1"}

    def exec_start(self, exec_id, **kwargs):
        self.exec_calls.append(("start", exec_id, kwargs))
        return SimpleNamespace(read=lambda n: b"", write=lambda d: len(d), close=lambda: None)

    def exec_resize(self, exec_id, **kwargs):
        self.exec_calls.append(("resize", exec_id, kwargs))

    def pull(self, name, tag=None, **kwargs):
        self.pull_calls.append((name, tag, kwargs))
        return iter([{"status": "Pulling", "id": None}])


@pytest.fixture
def container_service():
    collection = FakeContainersCollection()
    api = FakeLowLevelAPI()
    return ContainerService(collection, api), collection, api


async def test_container_list(container_service):
    svc, collection, _ = container_service
    items = await svc.list(all=True)
    assert items[0]["id"] == "abcdef1234"
    assert collection.list_all is True


async def test_container_item_not_found_returns_none(container_service):
    svc, _, _ = container_service
    assert await svc.item("missing") is None


async def test_container_create_converts_mappings(container_service):
    svc, collection, _ = container_service
    await svc.create(
        name="web", image="nginx", command="nginx", interactive=True, tty=True,
        privileged=True,
        ports=[{"port": 80, "protocol": "tcp", "listen_ip": "0.0.0.0", "listen_port": 8080}],
        volumes=[{"path": "data", "bind": "/data", "mode": "ro"}],
    )
    args, kwargs = collection.create_kwargs
    assert kwargs["stdin_open"] is True and kwargs["tty"] is True
    assert kwargs["privileged"] is True
    assert kwargs["ports"] == {"80/tcp": ("0.0.0.0", 8080)}
    assert kwargs["volumes"] == {"data": {"bind": "/data", "mode": "ro"}}


async def test_container_run_detaches(container_service):
    svc, collection, _ = container_service
    await svc.run(name="web", image="nginx", command="nginx")
    _, kwargs = collection.run_kwargs
    assert kwargs["detach"] is True


async def test_container_operations(container_service):
    svc, collection, _ = container_service
    await svc.remove("c1")
    await svc.start("c1")
    await svc.stop("c1", timeout=5)
    await svc.restart("c1", timeout=3)
    await svc.rename("c1", "new-name")
    calls = collection.obj.calls
    assert "remove" in calls and "start" in calls
    assert ("stop", 5) in calls and ("restart", 3) in calls
    assert ("rename", "new-name") in calls


async def test_container_exec_decodes_output(container_service):
    svc, collection, _ = container_service
    result = await svc.exec("c1", "ls", interactive=True, tty=True)
    assert result == {"exit_code": 0, "output": "total 0\n"}
    _, _, kwargs = collection.obj.calls[-1]
    assert kwargs["stdin"] is True and kwargs["tty"] is True


async def test_container_logs_parses_timestamps(container_service):
    svc, collection, _ = container_service
    text = await svc.logs("c1", since="1704067200", until=None)
    assert text == "log text\n"
    _, kwargs = collection.obj.calls[-1]
    assert kwargs["since"] == 1704067200 and kwargs["until"] is None


async def test_container_open_log_stream(container_service):
    svc, collection, _ = container_service
    stream = await svc.open_log_stream("c1", since=None, until=None, follow=True)
    assert list(stream) == [b"a\n", b"b\n"]
    _, kwargs = collection.obj.calls[-1]
    assert kwargs["stream"] is True and kwargs["follow"] is True


async def test_container_diff_groups_by_kind(container_service):
    svc, _, _ = container_service
    result = await svc.diff("c1")
    assert result == {
        "add": ["/new"],
        "change": ["/etc/passwd"],
        "delete": ["/gone"],
        "other": ["/weird"],
    }


async def test_container_diff_none(container_service, monkeypatch):
    svc, collection, _ = container_service
    collection.obj.diff = lambda: None
    result = await svc.diff("c1")
    assert result == {"add": [], "change": [], "delete": [], "other": []}


async def test_container_commit_returns_image(container_service):
    svc, _, _ = container_service
    image = await svc.commit("c1", "web-image", "v1", message="m", author="a")
    assert image["id"] == "0123456789ab"


async def test_container_terminal_helpers(container_service):
    svc, _, api = container_service
    assert await svc.get_status("c1") == "running"
    with pytest.raises(NotFound):
        await svc.get_status("missing")

    exec_id = await svc.exec_create_tty("c1", ["/bin/sh"])
    assert exec_id == "exec-1"
    sock = await svc.exec_start_socket(exec_id)
    assert sock.read(1) == b""
    await svc.exec_resize(exec_id, 24, 80)
    kinds = [c[0] for c in api.exec_calls]
    assert kinds == ["create", "start", "resize"]
    _, _, _, create_kwargs = api.exec_calls[0]
    assert create_kwargs == {"tty": True, "stdin": True}
    _, _, start_kwargs = api.exec_calls[1]
    assert start_kwargs == {"socket": True, "tty": True, "demux": False}


class FakeImagesCollection:
    def __init__(self):
        self.obj = make_image_obj()
        self.obj.tag = lambda name, tag: True
        self.obj.history = lambda: [
            {
                "Id": "sha256:0123456789abcdef",
                "CreatedBy": "/bin/sh -c #(nop) CMD",
                "Created": 1704067200,
                "Size": 0,
                "Tags": None,
                "Comment": "",
            },
        ]
        self.removed = []

    def list(self, all=False):
        return [self.obj]

    def get(self, id):
        if id == "missing":
            raise NotFound("no such image")
        return self.obj

    def search(self, keyword):
        return [{"name": keyword}]

    def remove(self, id, noprune=False):
        self.removed.append((id, noprune))


async def test_image_service():
    collection = FakeImagesCollection()
    api = FakeLowLevelAPI()
    svc = ImageService(collection, api)

    items = await svc.list()
    assert items[0]["tags"] == ["nginx:latest"]
    assert await svc.item("missing") is None
    assert (await svc.search("nginx")) == [{"name": "nginx"}]

    await svc.remove("i1", tag_only=True)
    assert collection.removed == [("i1", True)]

    assert await svc.tag("i1", "repo", "v1") is True

    history = await svc.history("i1")
    assert history[0]["id"] == "0123456789"
    assert history[0]["created_by"] == "/bin/sh -c #(nop) CMD"

    events = list(svc.pull_stream("nginx", "latest"))
    assert events[0]["status"] == "Pulling"
    assert api.pull_calls[-1][1] == "latest"

    list(svc.pull_stream("nginx", "*"))
    assert api.pull_calls[-1][1] is None

    list(svc.pull_stream("nginx", None))
    assert api.pull_calls[-1][1] == "latest"


class FakeNetworksCollection:
    def __init__(self):
        self.obj = make_network_obj()
        self.obj.remove = lambda: None
        self.connect_calls = []
        self.disconnect_calls = []
        self.obj.connect = lambda cid, ipv4_address=None: self.connect_calls.append(
            (cid, ipv4_address))
        self.obj.disconnect = lambda cid, force=False: self.disconnect_calls.append(
            (cid, force))
        self.create_kwargs = None

    def list(self, **kwargs):
        return [self.obj]

    def get(self, id):
        if id == "missing":
            raise NotFound("no such network")
        return self.obj

    def create(self, *args, **kwargs):
        self.create_kwargs = (args, kwargs)
        return self.obj


async def test_network_service():
    collection = FakeNetworksCollection()
    svc = NetworkService(collection)

    items = await svc.list(greedy=True)
    assert items[0]["name"] == "bridge"
    assert await svc.item("missing") is None

    await svc.create(
        name="net", driver="bridge", attachable=True,
        options=[{"key": "mtu", "value": "1500"}],
        subnet="10.0.0.0/24", gateway="10.0.0.1", ip_range=None,
    )
    args, kwargs = collection.create_kwargs
    assert kwargs["options"] == {"mtu": "1500"}
    assert kwargs["ipam"] is not None

    await svc.create(name="net2", driver="bridge")
    _, kwargs = collection.create_kwargs
    assert kwargs["ipam"] is None

    await svc.connect("n1", "c1", ipv4_address="10.0.0.5")
    assert collection.connect_calls == [("c1", "10.0.0.5")]
    await svc.disconnect("n1", "c1", force=True)
    assert collection.disconnect_calls == [("c1", True)]


class FakeVolumesCollection:
    def __init__(self):
        self.obj = make_volume_obj()
        self.obj.remove = lambda: None
        self.create_kwargs = None

    def list(self, **kwargs):
        return [self.obj]

    def get(self, id):
        if id == "missing":
            raise NotFound("no such volume")
        return self.obj

    def create(self, *args, **kwargs):
        self.create_kwargs = (args, kwargs)
        return self.obj


async def test_volume_service():
    collection = FakeVolumesCollection()
    svc = VolumeService(collection)

    items = await svc.list()
    assert items[0]["name"] == "data"
    assert await svc.item("missing") is None

    await svc.create(
        name="v1", driver="local",
        driver_opts=[{"key": "type", "value": "tmpfs"}],
    )
    _, kwargs = collection.create_kwargs
    assert kwargs["driver_opts"] == {"type": "tmpfs"}


async def test_docker_version(monkeypatch):
    client = SimpleNamespace(
        containers=FakeContainersCollection(),
        images=FakeImagesCollection(),
        networks=FakeNetworksCollection(),
        volumes=FakeVolumesCollection(),
        api=FakeLowLevelAPI(),
    )
    client.version = lambda: {
        "Version": "24.0.0",
        "ApiVersion": "1.43",
        "Components": [
            {"Name": "Engine", "Version": "24.0.0", "Details": {"ApiVersion": "1.43"}},
        ],
    }
    docker = Docker(client)
    version = await docker.version()
    assert "Engine" in version
    assert version["Engine"]["version"] == "24.0.0"
