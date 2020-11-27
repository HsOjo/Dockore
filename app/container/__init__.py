from flask import request

from app import common
from app.base.user_api_controller import UserAPIController


class Container(UserAPIController):
    import_name = __name__
    url_prefix = '/api/container'

    def __init__(self, app):
        super().__init__(app)

    def callback_add_routes(self):
        self.add_route('/list', self.list, methods=['POST'])
        self.add_route('/item/<string:id>', self.item, methods=['POST'])

    def list(self):
        try:
            data = request.get_json()  # type: dict
            is_all = data.get('is_all', True)
        except:
            raise self.ParamsNotMatchException

        docker = common.get_docker_cli()
        items = [{
            'id': container.attrs['Id'],
            'name': container.attrs['Name'],
            'image_id': container.attrs['Image'],
            'create_time': container.attrs['Created'],
        } for container in docker.containers.list(
            all=is_all
        )]
        return self.make_response(items=items)

    def item(self, id: str):
        docker = common.get_docker_cli()
        item = docker.containers.get(id)
        return self.make_response(item=item.attrs)
