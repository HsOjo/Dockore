from app.libs.docker_ import Docker


class ImageService:
    @staticmethod
    def list(is_all):
        return Docker().image.list(all=is_all)

    @staticmethod
    def item(id):
        return Docker().image.item(id)

    @staticmethod
    def delete(id):
        Docker().image.remove(id)

    @staticmethod
    def search(keyword):
        return Docker().image.search(keyword)

    @staticmethod
    def pull(name, tag):
        if not tag:
            tag = 'latest'
        if tag == '*':
            tag = None
        return Docker().image.pull(name, tag)
