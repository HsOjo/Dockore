import os

import docker
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app import common


class Application(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.docker = docker.from_env()
        common.current_app = self

        program_path = os.path.join(self.root_path, '..')
        config_path = os.path.join(program_path, 'config.py')
        if not os.path.exists(config_path):
            config_path = os.path.join(program_path, 'config.example.py')
        self.config.from_pyfile(config_path)
        os.makedirs(common.get_data_path(), exist_ok=True)

        db.init_app(self)
        cors.init_app(self)

        self.register_controllers()

    def register_controllers(self):
        from app.image import Image
        from app.container import Container
        from app.user import User

        Image(self)
        Container(self)
        User(self)


db = SQLAlchemy()
cors = CORS(supports_credentials=True)
app = Application()
migrate = Migrate(app, db)
