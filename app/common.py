from docker import DockerClient

from saika import Config


def get_docker_cli():
    docker = DockerClient(Config.section('docker').get('url'))
    return docker
