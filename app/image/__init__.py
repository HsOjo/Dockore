from app import common
from app.base.api import request_check
from app.base.controller.decorator import *
from app.image.request import ListRequest
from app.image.service import ImageService
from app.user.controller import UserAPIController


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
