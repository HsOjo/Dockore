import json

import pytest

from app.services.cli import (
    CliError,
    Docker,
    DockerApiError,
    DockerError,
    DockerNotFound,
)
from app.services.cli.container import ContainerService
from app.services.cli.docker_cli import map_cli_error
from app.services.cli.image import ImageService
from app.services.cli.network import NetworkService
from app.services.cli.volume import VolumeService
from tests.fakes import (
    make_container_attrs,
    make_image_attrs,
    make_network_attrs,
    make_volume_attrs,
)


def _cli_error(output, returncode=1):
    return CliError(["docker", "x"], returncode, output)


def test_map_cli_error_not_found():
    for text in ("Error: No such container: abc", "no such image", "not found"):
        assert isinstance(map_cli_error(_cli_error(text)), DockerNotFound)


def test_map_cli_error_daemon():
    for text in (
        "Cannot connect to the Docker daemon at unix:///var/run/docker.sock",
        "error during connect",
        "Is the docker daemon running?",
        "connection refused",
    ):
        err = map_cli_error(_cli_error(text))
        assert type(err) is DockerError


def test_map_cli_error_generic_api_error():
    err = map_cli_error(_cli_error("container is running: stop it first"))
    assert type(err) is DockerApiError


class FakeRunExecutor:
    """Records executor.run calls; programmable output or CliError."""

    def __init__(self, output="", error=None):
        self.output = output
        self.error = error
        self.calls = []

    async def run(self, args, cwd=None):
        self.calls.append(args)
        if self.error:
            raise self.error
        return self.output


class FakeCli:
    """DockerCli stand-in: records args, serves programmed inspect/ls data."""

    def __init__(self):
        self.calls = []
        self.run_output = ""
        self.run_error = None
        self.json_lines_rows = []
        self.inspect_map = {}
        self.inspect_list_handler = None
        self.executor = FakeRunExecutor()

    async def run(self, *args, cwd=None):
        self.calls.append(args)
        if self.run_error:
            raise self.run_error
        return self.run_output

    async def run_json_lines(self, *args):
        self.calls.append(args)
        return self.json_lines_rows

    async def inspect(self, *args):
        self.calls.append(args)
        key = args[-1]
        if key not in self.inspect_map:
            raise DockerNotFound(f"no such object: {key}")
        return self.inspect_map[key]

    async def inspect_list(self, *args):
        self.calls.append(args)
        if self.inspect_list_handler:
            return self.inspect_list_handler(args)
        return [self.inspect_map[a] for a in args]


@pytest.fixture
def cli():
    return FakeCli()


async def test_container_list(cli):
    cli.json_lines_rows = [{"ID": make_container_attrs()["Id"]}]

    def inspect_list(args):
        if args[0] == "image":
            return [make_image_attrs()]
        return [make_container_attrs()]

    cli.inspect_list_handler = inspect_list
    svc = ContainerService(cli)
    items = await svc.list(all=True)
    assert cli.calls[0] == ("ps", "--no-trunc", "--format", "{{json .}}", "--all")
    assert items[0]["id"] == "abcdef123456"
    assert items[0]["image"]["id"] == "0123456789ab"


async def test_container_item_not_found_returns_none(cli):
    svc = ContainerService(cli)
    assert await svc.item("missing") is None


async def test_container_create_command_args(cli):
    cli.run_output = "deadbeef\n"
    cli.inspect_map["deadbeef"] = make_container_attrs()
    cli.inspect_map[make_container_attrs()["Image"]] = make_image_attrs()
    svc = ContainerService(cli)
    item = await svc.create(
        name="web", image="nginx", command="nginx -g 'daemon off;'",
        interactive=True, tty=True, privileged=True,
        ports=[{"port": 80, "protocol": "tcp", "listen_ip": "0.0.0.0",
                "listen_port": 8080}],
        volumes=[{"path": "data", "bind": "/data", "mode": "ro"}],
    )
    assert item["id"] == "abcdef123456"
    assert cli.calls[0] == (
        "create", "--name", "web", "-i", "-t", "--privileged",
        "-p", "0.0.0.0:8080:80/tcp",
        "-v", "/data:data:ro",
        "nginx", "nginx", "-g", "daemon off;",
    )


async def test_container_run_detaches(cli):
    cli.run_output = "deadbeef\n"
    cli.inspect_map["deadbeef"] = make_container_attrs()
    cli.inspect_map[make_container_attrs()["Image"]] = make_image_attrs()
    svc = ContainerService(cli)
    await svc.run(name="web", image="nginx", command="nginx")
    assert cli.calls[0][:2] == ("run", "-d")


async def test_container_operations_args(cli):
    svc = ContainerService(cli)
    await svc.remove("c1")
    await svc.start("c1")
    await svc.stop("c1", timeout=5)
    await svc.restart("c1", timeout=3)
    await svc.rename("c1", "new-name")
    assert cli.calls == [
        ("rm", "c1"),
        ("start", "c1"),
        ("stop", "-t", "5", "c1"),
        ("restart", "-t", "3", "c1"),
        ("rename", "c1", "new-name"),
    ]


async def test_container_exec_decodes_output(cli):
    cli.executor.output = "total 0\n"
    svc = ContainerService(cli)
    result = await svc.exec("c1", "ls", interactive=True, privileged=True)
    assert result == {"exit_code": 0, "output": "total 0\n"}
    assert cli.executor.calls == [
        ["docker", "exec", "-i", "--privileged", "c1", "sh", "-c", "ls"]
    ]


async def test_container_exec_nonzero_exit(cli):
    cli.executor.error = CliError(["docker", "exec"], 2, "boom\n")
    svc = ContainerService(cli)
    result = await svc.exec("c1", "ls")
    assert result == {"exit_code": 2, "output": "boom\n"}


async def test_container_logs_args(cli):
    cli.run_output = "log text\n"
    svc = ContainerService(cli)
    text = await svc.logs("c1", since="1704067200", until="1704070800")
    assert text == "log text\n"
    assert cli.calls == [
        ("logs", "--since", "1704067200", "--until", "1704070800", "c1")
    ]


async def test_container_diff_groups_by_kind(cli):
    cli.run_output = "A /new\nC /etc/passwd\nD /gone\nX /weird\n"
    svc = ContainerService(cli)
    result = await svc.diff("c1")
    assert result == {
        "add": ["/new"],
        "change": ["/etc/passwd"],
        "delete": ["/gone"],
        "other": ["/weird"],
    }


async def test_container_diff_empty(cli):
    cli.run_output = ""
    svc = ContainerService(cli)
    assert await svc.diff("c1") == {
        "add": [], "change": [], "delete": [], "other": [],
    }


async def test_container_commit_args(cli):
    cli.inspect_map["web-image:v1"] = make_image_attrs()
    svc = ContainerService(cli)
    image = await svc.commit("c1", "web-image", "v1", message="m", author="a")
    assert cli.calls[0] == ("commit", "-m", "m", "-a", "a", "c1", "web-image:v1")
    assert image["id"] == "0123456789ab"


async def test_container_get_status(cli):
    cli.inspect_map["c1"] = make_container_attrs()
    svc = ContainerService(cli)
    assert await svc.get_status("c1") == "running"
    with pytest.raises(DockerNotFound):
        await svc.get_status("missing")


async def test_image_list_dedupes_ids(cli):
    cli.json_lines_rows = [
        {"ID": "sha256:" + "0123456789ab" + "0" * 52},
        {"ID": "sha256:" + "0123456789ab" + "0" * 52},
    ]
    cli.inspect_map["sha256:" + "0123456789ab" + "0" * 52] = make_image_attrs()
    svc = ImageService(cli)
    items = await svc.list(all=True)
    assert cli.calls[0] == (
        "image", "ls", "--no-trunc", "--format", "{{json .}}", "--all",
    )
    assert len(items) == 1
    assert items[0]["tags"] == ["nginx:latest"]


async def test_image_item_not_found_returns_none(cli):
    svc = ImageService(cli)
    assert await svc.item("missing") is None


async def test_image_search(cli):
    cli.json_lines_rows = [
        {
            "Name": "nginx",
            "Description": "Official build of Nginx.",
            "StarCount": "100",
            "IsOfficial": "[OK]",
            "IsAutomated": "",
        },
    ]
    svc = ImageService(cli)
    results = await svc.search("nginx")
    assert cli.calls[0] == ("search", "--format", "{{json .}}", "nginx")
    assert results == [
        {
            "name": "nginx",
            "description": "Official build of Nginx.",
            "star_count": 100,
            "is_official": True,
            "is_automated": False,
        },
    ]


async def test_image_remove_and_tag_args(cli):
    svc = ImageService(cli)
    await svc.remove("i1", tag_only=True)
    assert await svc.tag("i1", "repo", "v1") is True
    assert cli.calls == [("rmi", "i1"), ("tag", "i1", "repo:v1")]


async def test_image_history_parses_sizes(cli):
    cli.json_lines_rows = [
        {
            "ID": "sha256:0123456789abcdef",
            "CreatedBy": "/bin/sh -c #(nop) CMD",
            "CreatedAt": "2024-01-01T00:00:00Z",
            "Size": "10MB",
            "Comment": "",
        },
    ]
    svc = ImageService(cli)
    history = await svc.history("i1")
    assert cli.calls[0] == ("history", "--format", "{{json .}}", "i1")
    assert history[0]["id"] == "0123456789"
    assert history[0]["created_by"] == "/bin/sh -c #(nop) CMD"
    assert history[0]["size"] == 10_000_000


async def test_network_list(cli):
    cli.json_lines_rows = [{"ID": make_network_attrs()["Id"]}]
    cli.inspect_map[make_network_attrs()["Id"]] = make_network_attrs()
    svc = NetworkService(cli)
    items = await svc.list()
    assert cli.calls[0] == (
        "network", "ls", "--no-trunc", "--format", "{{json .}}",
    )
    assert items[0]["name"] == "bridge"


async def test_network_item_not_found_returns_none(cli):
    svc = NetworkService(cli)
    assert await svc.item("missing") is None


async def test_network_create_args(cli):
    cli.inspect_map["net"] = make_network_attrs()
    svc = NetworkService(cli)
    item = await svc.create(
        name="net", driver="bridge", attachable=True,
        options=[{"key": "mtu", "value": "1500"}],
        subnet="10.0.0.0/24", gateway="10.0.0.1", ip_range="10.0.0.0/25",
    )
    assert cli.calls[0] == (
        "network", "create", "--driver", "bridge",
        "--subnet", "10.0.0.0/24", "--gateway", "10.0.0.1",
        "--ip-range", "10.0.0.0/25", "--attachable",
        "--opt", "mtu=1500", "net",
    )
    assert item["name"] == "bridge"


async def test_network_connect_disconnect_args(cli):
    svc = NetworkService(cli)
    await svc.connect("n1", "c1", ipv4_address="10.0.0.5")
    await svc.disconnect("n1", "c1", force=True)
    assert cli.calls == [
        ("network", "connect", "--ip", "10.0.0.5", "n1", "c1"),
        ("network", "disconnect", "--force", "n1", "c1"),
    ]


async def test_volume_list(cli):
    cli.json_lines_rows = [{"Name": "data"}]
    cli.inspect_map["data"] = make_volume_attrs()
    svc = VolumeService(cli)
    items = await svc.list()
    assert cli.calls[0] == ("volume", "ls", "--format", "{{json .}}")
    assert items[0]["name"] == "data"


async def test_volume_item_not_found_returns_none(cli):
    svc = VolumeService(cli)
    assert await svc.item("missing") is None


async def test_volume_create_args(cli):
    cli.inspect_map["v1"] = make_volume_attrs()
    svc = VolumeService(cli)
    await svc.create(
        name="v1", driver="local",
        driver_opts=[{"key": "type", "value": "tmpfs"}],
    )
    assert cli.calls[0] == (
        "volume", "create", "--driver", "local",
        "--opt", "type=tmpfs", "--name", "v1",
    )


async def test_docker_version():
    class _VersionCli:
        async def run(self, *args, cwd=None):
            return json.dumps({
                "Server": {
                    "Version": "24.0.0",
                    "Components": [
                        {
                            "Name": "Engine",
                            "Version": "24.0.0",
                            "Details": {"ApiVersion": "1.43"},
                        },
                    ],
                },
            })

    docker = Docker("")
    docker.cli = _VersionCli()
    version = await docker.version()
    assert version["Docker"]["version"] == "24.0.0"
    assert version["Engine"]["version"] == "24.0.0"
    assert version["Engine"]["api_version"] == "1.43"
