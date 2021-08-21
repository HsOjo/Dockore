from saika.decorator import *

from .decorator import ignore_auth
from .enums import *
from .forms import *
from .user_api import UserAPIController


@controller
class User(UserAPIController):
    @ignore_auth
    @post
    @rule('/login')
    @form(LoginForm)
    def login(self):
        token = self.service_user.login(**self.form.data)
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
            role_type=user.role.type,
        )

    @post
    @rule('/change-password')
    @form(ChangePasswordForm)
    def change_password(self):
        result = self.service_user.change_password(self.current_user.username, **self.form.data)
        if not result:
            self.error(*CHANGE_PASSWORD_FAILED)

        self.success(*CHANGE_PASSWORD_SUCCESS)
