from app.user.enum import TOKEN_INVALID
from app.user.service import UserService
from saika.api import APIController

GK_USER = 'user'
HK_TOKEN = 'Token'


class UserAPIController(APIController):
    def callback_before_register(self):
        self.blueprint.before_request(self.callback_before_request)

    def callback_before_request(self):
        if self.request.method == 'OPTIONS':
            return

        token = self.request.headers.get(HK_TOKEN)
        user = UserService.get_user(token)
        self.context.g_set(GK_USER, user)

        if user is None:
            self.error(*TOKEN_INVALID)

    @property
    def current_user(self):
        return self.context.g_get(GK_USER)
