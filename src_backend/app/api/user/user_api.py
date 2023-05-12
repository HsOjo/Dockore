from saika import MetaTable, APIController
from saika.context import Context

from .enums import *
from .models import User, RoleShip
from .service import UserService

GK_USER = 'user'
HK_AUTH = 'Authorization'
MK_PUBLIC = 'public'
MK_ROLES = 'roles'


class UserAPIController(APIController):
    @property
    def service_user(self):
        return UserService()

    def callback_before_register(self):
        super().callback_before_register()

        @self.blueprint.before_request
        def authentication():
            if Context.request.method == 'OPTIONS':
                return ''

            f = Context.get_view_function()
            if f is None or MetaTable.get(f, MK_PUBLIC):
                return

            token = Context.request.headers.get(HK_AUTH)
            user = self.service_user.get_user(token)
            if user is None:
                self.error(*TOKEN_INVALID)

            if user.role.type != RoleShip.TYPE_ADMIN:
                roles = MetaTable.get(f, MK_ROLES, [])  # type: list
                if roles and user.role.type not in roles:
                    self.error(*ROLE_PERMISSION_DENIED)

            Context.g_set(GK_USER, user)

    @property
    def current_user(self):
        user = Context.g_get(GK_USER)  # type: User
        return user
