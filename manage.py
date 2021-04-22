from saika import init_manager

from app import app, commands

manager = init_manager(app)
commands.register(manager)

if __name__ == '__main__':
    manager.run()
