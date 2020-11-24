from app import common
from app.base.user_api_controller import UserAPIController


class Image(UserAPIController):
    import_name = __name__
    url_prefix = '/api/image'

    def __init__(self, app):
        super().__init__(app)

    def callback_add_routes(self):
        self.add_route('/list', self.list, methods=['POST'])

    def list(self):
        docker = common.get_docker_cli()
        images = [{
            'id': img.attrs['Id'],
            'author': img.attrs['Author'],
            'create_time': img.attrs['Created'],
            'size': img.attrs['Size'],
            'comment': img.attrs['Comment'],
        } for img in docker.images.list()]
        return self.make_response(images=images)
