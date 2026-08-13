import shlex
from typing import Dict, List, Optional

from app.core.validators import validate_docker_name, validate_image_ref, validate_no_dash
from .convertors import (
    MountsConvertor,
    PortMappingConvertor,
    PortsConvertor,
    VolumesMappingConvertor,
)
from .docker_cli import DockerCli
from .errors import DockerNotFound
from .executor import CliError


def image_item_from_inspect(data: dict, verbose: bool = False) -> dict:
    image_id = data.get("Id") or ""
    if image_id.startswith("sha256:"):
        image_id = image_id[7:]
    item = dict(
        id=image_id[:12],
        tags=data.get("RepoTags") or [],
        author=data.get("Author") or "",
        create_time=data.get("Created") or "",
        size=data.get("Size") or 0,
    )
    if verbose:
        cfg = data.get("Config") or {}
        if cfg.get("Cmd"):
            item.update(command=" ".join(cfg["Cmd"]))
        item.update(
            tty=cfg.get("Tty"),
            interactive=cfg.get("OpenStdin"),
            architecture=data.get("Architecture"),
            os=data.get("Os"),
            ports=PortsConvertor.from_docker(cfg.get("ExposedPorts")),
        )
    return item


def container_item_from_inspect(attrs: dict, image: dict, verbose: bool = False) -> dict:
    item = dict(
        id=(attrs.get("Id") or "")[:12],
        name=(attrs.get("Name") or "").lstrip("/"),
        image=image,
        create_time=attrs.get("Created") or "",
        status=(attrs.get("State") or {}).get("Status") or "",
    )
    if verbose:
        ns = attrs.get("NetworkSettings") or {}
        cfg = attrs.get("Config") or {}
        host_cfg = attrs.get("HostConfig") or {}
        networks = ns.get("Networks") or {}
        first = next(iter(networks.values()), {}) if networks else {}
        if cfg.get("Cmd"):
            item.update(command=" ".join(cfg["Cmd"]))
        item.update(
            tty=cfg.get("Tty"),
            interactive=cfg.get("OpenStdin"),
            network=dict(
                ip=first.get("IPAddress") or ns.get("IPAddress"),
                prefix=(
                    first.get("IPPrefixLen")
                    if first.get("IPPrefixLen") is not None
                    else ns.get("IPPrefixLen")
                ),
                gateway=first.get("Gateway") or ns.get("Gateway"),
                mac_address=first.get("MacAddress") or ns.get("MacAddress"),
                ports=PortMappingConvertor.from_docker(host_cfg.get("PortBindings")),
            ),
            mounts=MountsConvertor.from_docker(attrs.get("Mounts") or []),
        )
    return item


class ContainerService:
    """Container operations backed by the `docker` CLI."""

    def __init__(self, cli: DockerCli):
        self._cli = cli

    async def _image_item(self, ref: str, fallback_tag: Optional[str] = None,
                          verbose: bool = False) -> dict:
        try:
            return image_item_from_inspect(await self._cli.inspect("image", ref), verbose)
        except DockerNotFound:
            tags = [fallback_tag] if fallback_tag else []
            return dict(id="", tags=tags, author="", create_time="", size=0)

    async def _image_items(self, refs: Dict[str, Optional[str]]) -> Dict[str, dict]:
        keys = list(refs)
        try:
            data = await self._cli.inspect_list("image", *keys)
            if len(data) != len(keys):
                raise DockerNotFound("image inspect returned partial results")
            return {ref: image_item_from_inspect(d) for ref, d in zip(keys, data)}
        except DockerNotFound:
            return {ref: await self._image_item(ref, refs[ref]) for ref in keys}

    async def list(self, all: bool = False, verbose: bool = False):
        args = ["ps", "--no-trunc", "--format", "{{json .}}"]
        if all:
            args.append("--all")
        rows = await self._cli.run_json_lines(*args)
        if not rows:
            return []
        attrs_list = await self._cli.inspect_list("container", *[row["ID"] for row in rows])
        refs: Dict[str, Optional[str]] = {}
        for attrs in attrs_list:
            ref = attrs.get("Image") or ""
            if ref not in refs:
                refs[ref] = (attrs.get("Config") or {}).get("Image")
        images = await self._image_items(refs)
        return [
            container_item_from_inspect(attrs, images[attrs.get("Image") or ""], verbose)
            for attrs in attrs_list
        ]

    async def item(self, id: str):
        try:
            attrs = await self._cli.inspect("container", id)
        except DockerNotFound:
            return None
        image = await self._image_item(
            attrs.get("Image") or "", (attrs.get("Config") or {}).get("Image"),
        )
        return container_item_from_inspect(attrs, image, verbose=True)

    async def remove(self, id: str):
        await self._cli.run("rm", id)

    def _create_args(self, name, image, command, interactive, tty,
                     privileged, ports, volumes) -> List[str]:
        if name:
            name = validate_docker_name(name, "container name")
        image = validate_image_ref(image, "image")
        args: List[str] = []
        if name:
            args += ["--name", name]
        if interactive:
            args.append("-i")
        if tty:
            args.append("-t")
        if privileged:
            args.append("--privileged")
        args += PortMappingConvertor.to_cli_args(ports)
        args += VolumesMappingConvertor.to_cli_args(volumes)
        args.append(image)
        if command and command.strip():
            args += shlex.split(command)
        return args

    async def create(self, name, image, command, interactive=False, tty=False,
                     privileged=False, ports=None, volumes=None):
        output = await self._cli.run(
            "create",
            *self._create_args(name, image, command, interactive, tty,
                               privileged, ports, volumes),
        )
        # stderr warnings are merged into output; the id is the last line
        return await self.item(output.strip().splitlines()[-1])

    async def run(self, name, image, command, interactive=False, tty=False,
                  privileged=False, ports=None, volumes=None):
        output = await self._cli.run(
            "run", "-d",
            *self._create_args(name, image, command, interactive, tty,
                               privileged, ports, volumes),
        )
        return await self.item(output.strip().splitlines()[-1])

    async def start(self, id: str):
        await self._cli.run("start", id)

    async def stop(self, id: str, timeout: Optional[int] = None):
        args = ["stop"]
        if timeout is not None:
            args += ["-t", str(timeout)]
        await self._cli.run(*args, id)

    async def restart(self, id: str, timeout: Optional[int] = None):
        args = ["restart"]
        if timeout is not None:
            args += ["-t", str(timeout)]
        await self._cli.run(*args, id)

    async def rename(self, id: str, name: str):
        name = validate_docker_name(name, "container name")
        await self._cli.run("rename", id, name)

    async def exec(self, id: str, command, interactive=False, tty=False,
                   privileged=False, binary=False):
        # -t is intentionally not forwarded: a pty mixes control chars into output
        args = ["docker", "exec"]
        if interactive:
            args.append("-i")
        if privileged:
            args.append("--privileged")
        args += [id, "sh", "-c", command]
        try:
            output = await self._cli.executor.run(args)
            return dict(exit_code=0, output=output)
        except CliError as e:
            return dict(exit_code=e.returncode, output=e.output)

    async def logs(self, id: str, since=None, until=None):
        args = ["logs"]
        if since is not None:
            args += ["--since", since]
        if until is not None:
            args += ["--until", until]
        return await self._cli.run(*args, id)

    async def get_status(self, id: str):
        attrs = await self._cli.inspect("container", id)
        return (attrs.get("State") or {}).get("Status") or ""

    async def diff(self, id: str):
        result = dict(add=[], change=[], delete=[], other=[])
        kinds = {"A": result["add"], "C": result["change"], "D": result["delete"]}
        output = await self._cli.run("container", "diff", id)
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            kind, _, path = line.partition(" ")
            kinds.get(kind, result["other"]).append(path)
        return result

    async def commit(self, id: str, name, tag, message=None, author=None):
        name = validate_docker_name(name, "image name")
        if tag:
            tag = validate_no_dash(tag, "tag")
        if message:
            message = validate_no_dash(message, "message")
        if author:
            author = validate_no_dash(author, "author")
        args = ["commit"]
        if message:
            args += ["-m", message]
        if author:
            args += ["-a", author]
        ref = f"{name}:{tag}" if tag else name
        await self._cli.run(*args, id, ref)
        return image_item_from_inspect(await self._cli.inspect("image", ref), verbose=True)
