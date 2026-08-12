from .container import ContainerService
from .convertors import dict_to_lower, remove_empty_obj
from .docker_cli import DockerCli
from .image import ImageService
from .network import NetworkService
from .stack import StackDiscovery
from .volume import VolumeService


class Docker:
    """Facade grouping the per-resource CLI services for one docker_host."""

    def __init__(self, docker_host: str = ""):
        self.cli = DockerCli(docker_host)
        self.container = ContainerService(self.cli)
        self.image = ImageService(self.cli)
        self.network = NetworkService(self.cli)
        self.volume = VolumeService(self.cli)
        self.stack = StackDiscovery(self.cli)

    async def version(self):
        import json

        raw = await self.cli.run("version", "--format", "{{json .}}")
        data = json.loads(raw)
        version = dict_to_lower(data.get('Server') or data)
        version['name'] = 'Docker'
        components = [version]
        for c in version.pop('components', None) or []:
            details = c.pop('details', None) or {}
            c.update(details)
            components.append(c)
        result = {c.pop('name'): c for c in components}
        return remove_empty_obj(result)
