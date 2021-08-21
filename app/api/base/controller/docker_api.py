import traceback

from docker.errors import APIError, DockerException
from saika import Config, APIException

from app.api.enums import DOCKER_CAN_NOT_CONNECT
from app.api.user.user_api import UserAPIController
from app.config.docker import DockerConfig
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

    @property
    def docker(self):
        config = Config.get(DockerConfig)  # type: DockerConfig
        return Docker(config.url)
