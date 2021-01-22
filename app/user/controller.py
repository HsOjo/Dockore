from flask import request

from app.base.api import APIController, APIErrorException
from app.user.enum import TOKEN_INVALID
from app.user.service import UserService


class UserAPIController(APIController):
    def hook_before_view(self):
        data = request.get_json()  # type: dict
        token = data.get('token')
        user = UserService.get_user(token)
        if user is None:
            raise APIErrorException(*TOKEN_INVALID)
