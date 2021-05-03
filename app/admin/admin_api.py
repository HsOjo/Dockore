from app.base import DockerAPIController
from app.user import UserAPIController, RoleShip
from app.user.enums import ROLE_PERMISSION_DENIED


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
            if self.current_user.role.type != RoleShip.TYPE_ADMIN:
                self.error(*ROLE_PERMISSION_DENIED)
