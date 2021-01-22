from app.base.api import request_check
from app.base.controller.decorator import *
from app.user.controller import UserAPIController
from .enum import *
from .request import *
from .service import *


class Image(UserAPIController):
    import_name = __name__
    url_prefix = '/api/image'

    @post
    @mapping_rule('/list')
    @request_check(ListRequest)
    def list(self):
        data = common.get_req_data()

        return self.make_response(
            items=ImageService.list(data.get('is_all', False))
        )

    @post
    @mapping_rule('/item/<string:id>')
    def item(self, id_):
        return self.make_response(
            item=ImageService.item(id_)
        )

    @post
    @mapping_rule('/delete')
    @request_check(DeleteRequest)
    def delete(self):
        data = common.get_req_data()

        success = []
        error = []

        for id_ in data.get('ids'):
            if ImageService.delete(id_):
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
