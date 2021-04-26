import platform

from saika import Config, Environ
from saika.decorator import *
from saika.form import AUTO

from app.base import DockerAPIController
from .enums import *
from .forms import *
from ..const import Const


@controller('/api/system')
class System(DockerAPIController):
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

    @get
    @rule('/version')
    def version(self):
        uname = platform.uname()
        version = {Const.project: dict(
            version=Const.version,
            hostname=uname.node,
            py_version=platform.python_version(),
            os=uname.system,
            arch=uname.machine,
            kernel_version=uname.release,
        )}
        version.update(self.docker.version)
        self.success(version=version)
