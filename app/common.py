import os

from docker import DockerClient
from flask import Config, Flask, request

current_app: Flask


def get_config(key, default=None):
    config = current_app.config  # type: Config
    return config.get(key, default)


def get_program_path():
    app_path = current_app.root_path  # type: str
    path = os.path.join(app_path, '..')
    return path


def get_data_path():
    return os.path.join(get_program_path(), get_config('DATA_DIR'))


def get_docker_cli():
    docker = DockerClient(get_config('DOCKER_URL'))
    return docker


def get_req_data() -> dict:
    return request.get_json()
