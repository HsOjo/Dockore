from docker.models.images import ImageCollection, Image

from .collection import CollectionAdapter


class ImageAdapter(CollectionAdapter):
    _c: ImageCollection

    def _item(self, id):
        item = self._c.get(id)  # type: Image
        return item

    @staticmethod
    def convert(obj, verbose=False):
        item = dict(
            id=obj.short_id,
            tags=obj.tags,
            author=obj.attrs['Author'],
            create_time=obj.attrs['Created'],
            size=obj.attrs['Size'],
        )
        if verbose:
            cfg = obj.attrs['Config']
            item.update(
                command=' '.join(cfg['Cmd']),
                tty=cfg['Tty'],
                interactive=cfg['OpenStdin'],
                architecture=obj.attrs['Architecture'],
                os=obj.attrs['Os'],
            )
        return item

    def search(self, keyword):
        return self._c.search(keyword)

    def remove(self, id):
        self._c.remove(id)

    def pull(self, name, tag):
        if not tag:
            tag = 'latest'
        if tag == '*':
            tag = None
        item = self._c.pull(name, tag)
        return self.convert(item, True)

    def tag(self, id, name, tag):
        return self._c.get(id).tag(name, tag)
