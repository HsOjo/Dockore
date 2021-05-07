import traceback

from docker.errors import APIError, DockerException
from saika import Config, APIException

from app.api.enums import DOCKER_CAN_NOT_CONNECT
from app.api.user import UserAPIController
from app.libs import Docker

GK_DOCKER = 'docker'


class DockerAPIController(UserAPIController):
    def callback_before_register(self):
        super().callback_before_register()

        @self.blueprint.errorhandler(DockerException)
        def handle_connect(e):
            if 'Error while fetching server API version' in str(e):
                return APIException(*DOCKER_CAN_NOT_CONNECT)
            return e

        @self.blueprint.errorhandler(APIError)
        def catch(e):
            traceback.print_exc()
            return APIException(msg=e)

        @self.blueprint.before_request
        def init_docker():
            self.context.g_set(
                GK_DOCKER, Docker(Config.section('docker').get('url'))
            )

    @property
    def docker(self):
        docker = self.context.g_get(GK_DOCKER)  # type: Docker
        return docker
