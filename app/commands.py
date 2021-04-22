from flask_script import Manager

from app.user.service import UserService


def register(manager: Manager):
    @manager.command
    def register_user():
        username = input('Input Username: ')
        password = input('Input Password: ')
        try:
            UserService.register(username, password)
            print('Register success.')
        except Exception as e:
            print('Register failed.')
            raise e
