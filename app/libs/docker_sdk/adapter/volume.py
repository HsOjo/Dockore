from docker.models.volumes import VolumeCollection, Volume

from .collection import CollectionAdapter
from ..convertor import VolumeConvertor, OptionConvertor


class VolumeAdapter(CollectionAdapter):
    _c: VolumeCollection

    def _item(self, id):
        item = self._c.get(id)  # type: Volume
        return item

    @staticmethod
    def convert(obj, verbose=False):
        return VolumeConvertor.from_docker(obj, verbose)

    def remove(self, id):
        self._item(id).remove()

    def create(self, name, driver=None, driver_opts=None):
        item = self._c.create(name, driver=driver, driver_opts=OptionConvertor.to(driver_opts))
        return self.convert(item, verbose=True)
