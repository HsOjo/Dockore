from app.base.api import request_check, APIController
from app.base.controller.decorator import *
from .enum import *
from .request import LoginRequest
from .service import UserService
from .. import common


class User(APIController):
    import_name = __name__
    url_prefix = '/api/user'

    @post
    @mapping_rule('/login')
    @request_check(LoginRequest)
    def login(self):
        data = common.get_req_data()

        token = UserService.login(data['username'], data['password'])
        if not token:
            return self.make_response(*LOGIN_FAILED)

        return self.make_response(
            *LOGIN_SUCCESS, token=token.content,
        )
