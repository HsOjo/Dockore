import click
from saika.controller.cli import CliController
from saika.decorator import *

from app.api.admin.user.service import AdminUserService
from app.api.user.models import RoleShip


@doc('User Commands')
@controller
class UserCli(CliController):
    @property
    def service_admin_user(self):
        return AdminUserService()

    @doc('Add User', 'Add user from CLI.')
    @command
    @click.argument('username')
    @click.argument('password')
    @click.option('--is-admin', is_flag=True)
    def add(self, username: str, password: str, is_admin: bool):
        try:
            role_type = RoleShip.TYPE_ADMIN if is_admin else RoleShip.TYPE_USER
            self.service_admin_user.add(username, password, role_type)
            click.echo('Register success.')
        except Exception as e:
            raise e

    @doc('User Login', 'Login from CLI, return the user token.')
    @command
    @click.argument('username')
    @click.argument('password')
    @click.option('--expires', type=int, default=0, help='Expires time, Unit: Second')
    def login(self, username: str, password: str, expires: int):
        if expires <= 0:
            expires = None

        token = self.service_admin_user.login(username, password, expires)
        click.echo(token)
