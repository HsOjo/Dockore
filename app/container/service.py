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
        Docker().container.remove(id)

    @staticmethod
    def create(name, image, command):
        return Docker().container.create(name, image, command)

    @staticmethod
    def start(id):
        Docker().container.start(id)

    @staticmethod
    def stop(id):
        Docker().container.stop(id)

    @staticmethod
    def restart(id):
        Docker().container.restart(id)
