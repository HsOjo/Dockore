from docker import DockerClient

from saika import Config


def get_docker_cli():
    docker = DockerClient(Config.get('docker').get('url'))
    return docker
