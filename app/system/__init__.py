import platform

from saika.decorator import *

from app.base import DockerAPIController
from ..const import Const


@controller('/api/system')
class System(DockerAPIController):
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
