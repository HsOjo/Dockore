import traceback

from docker.errors import APIError
from saika import Config, APIException

from app.libs import Docker
from app.user import UserAPIController

GK_DOCKER = 'docker'


class DockerAPIController(UserAPIController):
    def callback_before_register(self):
        super().callback_before_register()

        @self.blueprint.errorhandler(APIError)
        def catch(e: APIError):
            traceback.print_exc()
            return APIException(msg=str(e))

    def callback_auth_success(self):
        self.context.g_set(
            GK_DOCKER, Docker(Config.section('docker').get('url'))
        )

    @property
    def docker(self):
        docker = self.context.g_get(GK_DOCKER)  # type: Docker
        return docker
