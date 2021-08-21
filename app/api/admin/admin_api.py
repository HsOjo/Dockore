from app.api.base import DockerAPIController
from app.api.user.user_api import UserAPIController
from app.api.user.models import  RoleShip
from app.api.user.enums import ROLE_PERMISSION_DENIED


class AdminAPIController(UserAPIController):
    def callback_before_register(self):
        super().callback_before_register()

        @self.blueprint.before_request
        def authentication():
            if not self.current_user or self.current_user.role.type != RoleShip.TYPE_ADMIN:
                self.error(*ROLE_PERMISSION_DENIED)


class DockerAdminAPIController(DockerAPIController):
    def callback_before_register(self):
        super().callback_before_register()

        @self.blueprint.before_request
        def authentication():
            if not self.current_user or self.current_user.role.type != RoleShip.TYPE_ADMIN:
                self.error(*ROLE_PERMISSION_DENIED)
