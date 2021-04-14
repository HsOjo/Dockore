import importlib
import os
import pkgutil

from flask import Flask

from . import hard_code
from .config import Config
from .const import Const
from .database import db
from .environ import Environ
from .meta_table import MetaTable


class SaikaApp(Flask):
    def __init__(self):
        super().__init__(self.__class__.__module__)
        self._init_env()
        self._import_modules()

        Config.load(Environ.config_path)
        cfg = Config.merge()
        self.config.from_mapping(cfg)
        self._init_app()

        self.controllers = []

        controllers = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_CONTROLLERS, [])
        for controller in controllers:
            c = controller()
            c.register(self)
            self.controllers.append(c)

    def _init_env(self):
        if Environ.app is not None:
            raise Exception('SaikaApp was created.')

        Environ.app = self
        Environ.program_path = os.path.join(self.root_path, '..')
        Environ.config_path = os.path.join(Environ.program_path, Const.config_file)
        Environ.data_path = os.path.join(Environ.program_path, Const.data_dir)

    def _init_app(self):
        db.init_app(self)

    def _import_modules(self):
        module = self.__class__.__module__
        sub_modules = list(pkgutil.iter_modules([module], '%s.' % module))
        sub_modules = [i.name for i in sub_modules if i.ispkg]
        for i in sub_modules:
            importlib.import_module(i)
