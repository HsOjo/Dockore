from docker import DockerClient

from .adapter import ImageAdapter, ContainerAdapter
from .utils import dict_to_lower, remove_empty_obj


class Docker:
    def __init__(self, url):
        self._cli = DockerClient(url)
        self.image = ImageAdapter(self._cli.images)
        self.container = ContainerAdapter(self._cli.containers)

    @property
    def version(self):
        version = dict_to_lower(self._cli.version())
        version['name'] = 'Docker'
        components = version.pop('components')  # type: list
        for c in components:
            c.update(c.pop('details'))
        components.insert(0, version)
        result = {c.pop('name'): c for c in components}
        result = remove_empty_obj(result)
        return result
