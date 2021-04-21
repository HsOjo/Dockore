from app.libs.docker_sdk import Docker
from saika import Config
from app.user.user_api import UserAPIController

GK_DOCKER = 'docker'


class DockerAPIController(UserAPIController):
    def callback_auth_success(self):
        self.context.g_set(
            GK_DOCKER, Docker(Config.section('docker').get('url'))
        )

    @property
    def docker(self):
        docker = self.context.g_get(GK_DOCKER)  # type: Docker
        return docker
