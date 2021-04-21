from docker.models.resource import Collection


class CollectionAdapter:
    def __init__(self, c: Collection):
        self._c = c

    def item(self, id):
        item = self._item(id)
        item = self._convert(item, verbose=True)
        return item

    def list(self, verbose=False, **kwargs):
        items = self._c.list(**kwargs)
        items = [self._convert(i, verbose) for i in items]
        return items

    def _convert(self, obj, verbose=False):
        pass

    def _item(self, id):
        pass
