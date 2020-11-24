from flask import request

from app.user.service import UserService
from .api_controller import APIController, APIErrorException


class TokenInvalidException(APIErrorException):
    code = -3
    msg = 'Token无效，请重新登录。'


class UserAPIController(APIController):
    def hook_before_view(self):
        data = request.get_json()  # type: dict
        token = data.get('token')
        user = UserService.get_user(token)
        if user is None:
            raise TokenInvalidException
