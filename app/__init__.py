import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import docker
from app import common


class Application(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.docker = docker.from_env()
        common.current_app = self

        program_path = os.path.join(self.root_path, '..')
        self.config.from_pyfile(os.path.join(program_path, 'config.py'))
        os.makedirs(common.get_data_path(), exist_ok=True)


        db.init_app(self)

        self.register_controllers()

    def register_controllers(self):
        from app.image import Image
        from app.container import Container
        from app.user import User

        Image(self)
        Container(self)
        User(self)


db = SQLAlchemy()
app = Application()
migrate = Migrate(app, db)
