import platform

from saika import Const as SaikaConst
from saika.decorator import *

from app.api.base import DockerAPIController
from app.const import Const


@controller()
class System(DockerAPIController):
    @get
    @rule('/version')
    def version(self):
        uname = platform.uname()
        version = {Const.project: dict(
            version=Const.version,
            hostname=uname.node,
            py_version=platform.python_version(),
            saika_version=SaikaConst.version,
            os=uname.system,
            arch=uname.machine,
            kernel_version=uname.release,
        )}
        version.update(self.docker.version)
        self.success(version=version)
