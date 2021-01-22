from app.base.api import request_check
from app.base.controller.decorator import *
from app.user.controller import UserAPIController
from .enum import *
from .request import *
from .service import *


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
            *(DELETE_SUCCESS if len(error) == 0 else DELETE_FAILED),
            result=dict(
                success=success,
                error=error,
            )
        )
