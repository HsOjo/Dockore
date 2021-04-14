from saika.api import APIController
from saika.decorator import *
from .enum import *
from .forms import LoginForm
from .service import UserService


@controller('/api/user')
class User(APIController):
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
