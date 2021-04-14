from app.user.enum import TOKEN_INVALID
from app.user.models import User
from app.user.service import UserService
from saika import MetaTable
from saika.api import APIController
from saika.context import Context

GK_USER = 'user'
HK_TOKEN = 'Token'
MK_PUBLIC = 'public'


def ignore_auth(f):
    MetaTable.set(f, MK_PUBLIC, True)
    return f


class UserAPIController(APIController):
    def callback_before_register(self):
        self.blueprint.before_request(self.callback_before_request)

    def callback_before_request(self):
        if self.request.method == 'OPTIONS':
            return

        f = Context.view_function()
        if f is None or MetaTable.get(f, MK_PUBLIC):
            return

        token = self.request.headers.get(HK_TOKEN)
        user = UserService.get_user(token)
        if user is None:
            self.error(*TOKEN_INVALID)

        self.context.g_set(GK_USER, user)

    @property
    def current_user(self):
        user = self.context.g_get(GK_USER)  # type: User
        return user
