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
        try:
            Docker().image.remove(id)
        except:
            return False

        return True
