from saika import Config, Environ
from saika.decorator import *
from saika.form import AUTO

from app.api.user import role_auth, RoleShip
from .enums import *
from .forms import *
from ..admin_api import AdminAPIController


@controller()
class AdminSystem(AdminAPIController):
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
                Environ.app.reload()
            except Exception as e:
                self.error(*CONFIG_FAILED, exc=e)
            self.success(*CONFIG_SUCCESS)
