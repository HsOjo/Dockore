from flask import request

from app.base.api_controller import APIController, APIErrorException
from .service import UserService


class User(APIController):
    import_name = __name__
    url_prefix = '/api/user'

    class LoginFailedException(APIErrorException):
        code = 1001
        msg = '登录失败，用户名或密码错误。'

    def __init__(self, app):
        super().__init__(app)

    def callback_add_routes(self):
        self.add_route('/login', self.login, methods=['POST'])

    def login(self):
        try:
            data = request.get_json()  # type: dict
            username = data['username']
            password = data['password']
        except:
            raise self.ParamsNotMatchException

        token = UserService.login(username, password)
        if not token:
            raise self.LoginFailedException

        return self.make_response(
            msg='登录成功',
            token=token.content,
        )
