from flask import request

from app import common
from app.base.user_api_controller import UserAPIController


class Image(UserAPIController):
    import_name = __name__
    url_prefix = '/api/image'

    def __init__(self, app):
        super().__init__(app)

    def callback_add_routes(self):
        self.add_route('/list', self.list, methods=['POST'])
        self.add_route('/item/<string:id>', self.item, methods=['POST'])

    def list(self):
        try:
            data = request.get_json()  # type: dict
            is_all = data.get('is_all', False)
        except:
            raise self.ParamsNotMatchException

        docker = common.get_docker_cli()
        items = [{
            'id': img.attrs['Id'],
            'author': img.attrs['Author'],
            'create_time': img.attrs['Created'],
            'size': img.attrs['Size'],
            'comment': img.attrs['Comment'],
        } for img in docker.images.list(
            all=is_all
        )]
        return self.make_response(items=items)

    def item(self, id: str):
        docker = common.get_docker_cli()
        item = docker.images.get(id)
        return self.make_response(item=item.attrs)
