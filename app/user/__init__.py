from saika.decorator import *

from .enums import *
from .forms import *
from .models import RoleShip, OwnerShip
from .service import UserService
from .user_api import UserAPIController, ignore_auth, role_auth


@controller('/api/user')
class User(UserAPIController):
    @ignore_auth
    @post
    @rule('/login')
    @form(LoginForm)
    def login(self):
        token = UserService.login(**self.form.data)
        if not token:
            self.error(*LOGIN_FAILED)

        self.success(*LOGIN_SUCCESS, token=token)

    @get
    @rule('/info')
    def info(self):
        user = self.current_user
        self.success(
            id=user.id,
            username=user.username,
            role=user.role.type,
        )

    @post
    @rule('/change_password')
    @form(ChangePasswordForm)
    def change_password(self):
        result = UserService.change_password(self.current_user.username, **self.form.data)
        if not result:
            self.error(*CHANGE_PASSWORD_FAILED)

        self.success(*CHANGE_PASSWORD_SUCCESS)
