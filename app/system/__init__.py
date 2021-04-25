from saika import Config, Environ
from saika.decorator import *
from saika.form import AUTO

from app.user import UserAPIController
from .enums import *
from .forms import *


@controller('/api/system')
class System(UserAPIController):
    @get
    @post
    @rule('/config')
    @form(ConfigForm, AUTO)
    def config(self):
        if self.request.method == 'GET':
            self.success(config=Config.all())
        elif self.request.method == 'POST':
            try:
                Config.all().update(**self.form.config.data)
                Config.save(Environ.config_path)
                return self.response(*CONFIG_SUCCESS)
            except Exception as e:
                self.error(*CONFIG_FAILED, exc=str(e))
