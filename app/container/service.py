from app import common


class ContainerService:
    @staticmethod
    def list(is_all):
        docker = common.get_docker_cli()
        items = [{
            'id': container.attrs['Id'],
            'name': container.attrs['Name'],
            'image_id': container.attrs['Image'],
            'create_time': container.attrs['Created'],
        } for container in docker.containers.list(
            all=is_all
        )]
        return items

    @staticmethod
    def item(id_):
        docker = common.get_docker_cli()
        item = docker.containers.get(id_)
        return item.attrs

    @staticmethod
    def delete(id):
        docker = common.get_docker_cli()
        try:
            docker.containers.get(id).remove()
        except:
            return False

        return True
