from app import common


class ImageService:
    @staticmethod
    def list(is_all):
        docker = common.get_docker_cli()
        items = [{
            'id': img.attrs['Id'],
            'tags': img.attrs['RepoTags'],
            'author': img.attrs['Author'],
            'create_time': img.attrs['Created'],
            'size': img.attrs['Size'],
        } for img in docker.images.list(
            all=is_all
        )]
        return items

    @staticmethod
    def item(id_):
        docker = common.get_docker_cli()
        item = docker.images.get(id_)
        return item.attrs

    @staticmethod
    def delete(id):
        docker = common.get_docker_cli()
        try:
            docker.images.get(id).remove()
        except:
            return False

        return True
