from app import common
from app.base.api import request_check
from app.container.request import ListRequest, DeleteRequest
from app.container.service import ContainerService
from app.user.controller import UserAPIController
from app.base.controller.decorator import *


class Container(UserAPIController):
    import_name = __name__
    url_prefix = '/api/container'

    @post
    @mapping_rule('/list')
    @request_check(ListRequest)
    def list(self):
        data = common.get_req_data()
        return self.make_response(
            items=ContainerService.list(data.get('is_all', True))
        )

    @post
    @mapping_rule('/item/<string:id_>')
    def item(self, id_: str):
        return self.make_response(
            item=ContainerService.item(id_)
        )

    @post
    @mapping_rule('/delete')
    @request_check(DeleteRequest)
    def delete(self):
        data = common.get_req_data()

        success = []
        error = []

        for id_ in data.get('ids'):
            if ContainerService.delete(id_):
                success.append(id_)
            else:
                error.append(id_)

        return self.make_response(
            result=dict(
                success=success,
                error=error,
            )
        )
