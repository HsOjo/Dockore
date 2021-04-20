from saika.decorator import *
from .enum import *
from .forms import LoginForm
from .service import UserService
from .user_api import UserAPIController, ignore_auth


@register_controller('/api/user')
class User(UserAPIController):
    @ignore_auth
    @post
    @rule('/login')
    @form(LoginForm)
    def login(self):
        username = self.form.username.data
        password = self.form.password.data

        token = UserService.login(username, password)
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
        )
