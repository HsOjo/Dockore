from app import common
from app.base.user_api_controller import UserAPIController


class Container(UserAPIController):
    import_name = __name__
    url_prefix = '/api/container'

    def __init__(self, app):
        super().__init__(app)

    def callback_add_routes(self):
        self.add_route('/list', self.list, methods=['POST'])

    def list(self):
        
        docker = common.get_docker_cli()
        images = [{
            'id': container.attrs['Id'],
            'name': container.attrs['Name'],
            'image_id': container.attrs['Image'],
            'create_time': container.attrs['Created'],
        } for container in docker.containers.list()]
        return self.make_response(images=images)
