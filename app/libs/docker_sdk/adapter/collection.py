from docker.errors import NotFound
from docker.models.resource import Collection


class CollectionAdapter:
    def __init__(self, c: Collection):
        self._c = c

    def item(self, id):
        try:
            item = self._item(id)
            item = self.convert(item, verbose=True)
        except NotFound:
            return None
        return item

    def list(self, verbose=False, **kwargs):
        items = self._c.list(**kwargs)
        items = [self.convert(i, verbose) for i in items]
        return items

    @staticmethod
    def convert(obj, verbose=False):
        pass

    def _item(self, id):
        pass
