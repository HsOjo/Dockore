from flask_migrate import MigrateCommand
from flask_script import Manager

from app import app
from app.user.service import UserService

manager = Manager(app)
manager.add_command('db', MigrateCommand)


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


if __name__ == '__main__':
    manager.run()
