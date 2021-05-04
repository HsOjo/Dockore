from saika import Config, Environ
from saika.decorator import *
from saika.form import AUTO

from app.api.user import role_auth, RoleShip
from .enums import *
from .forms import *
from ..admin_api import DockerAdminAPIController


@controller()
class AdminSystem(DockerAdminAPIController):
    @get
    @post
    @rule('/config')
    @form(ConfigForm, AUTO)
    @role_auth(RoleShip.TYPE_ADMIN)
    def config(self):
        if self.request.method == 'GET':
            self.success(config=Config.all())
        elif self.request.method == 'POST':
            try:
                cfgs = Config.all()
                for k, v in self.form.config.data.items():
                    cfgs[k].update(v)
                Config.save(Environ.config_path)
                return self.response(*CONFIG_SUCCESS)
            except Exception as e:
                self.error(*CONFIG_FAILED, exc=str(e))