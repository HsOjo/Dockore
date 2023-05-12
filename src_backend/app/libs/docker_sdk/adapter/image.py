from docker.models.images import ImageCollection, Image

from .collection import CollectionAdapter
from ..convertor import ImageConvertor, HistoriesConvertor


class ImageAdapter(CollectionAdapter):
    _c: ImageCollection

    def _item(self, id):
        item = self._c.get(id)  # type: Image
        return item

    @staticmethod
    def convert(obj, verbose=False):
        return ImageConvertor.from_docker(obj, verbose)

    def search(self, keyword):
        return self._c.search(keyword)

    def remove(self, id, tag_only=False):
        self._c.remove(id, noprune=tag_only)

    def pull(self, name, tag):
        if not tag:
            tag = 'latest'
        if tag == '*':
            tag = None
        item = self._c.pull(name, tag)
        return self.convert(item, True)

    def tag(self, id, name, tag):
        return self._c.get(id).tag(name, tag)

    def history(self, id):
        return HistoriesConvertor.from_docker(self._c.get(id).history())
