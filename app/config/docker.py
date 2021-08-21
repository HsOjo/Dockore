from saika import BaseConfig
from saika.decorator import config


@config
class DockerConfig(BaseConfig):
    url = "unix:///var/run/docker.sock"
    cli_bin = 'docker'
    terminal_expires = 3600