from app.libs.docker_ import Docker


class ContainerService:
    @staticmethod
    def list(is_all: bool):
        return Docker().container.list(all=is_all)

    @staticmethod
    def item(id):
        return Docker().container.item(id)

    @staticmethod
    def delete(id):
        try:
            Docker().container.remove(id)
        except:
            return False

        return True

    @staticmethod
    def create(name, image, command):
        return Docker().container.create(name, image, command)
