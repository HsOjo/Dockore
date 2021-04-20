import re

from flask import Blueprint

from . import hard_code
from .context import Context
from .meta_table import MetaTable


class Controller:
    def __init__(self, app):
        name = self.__class__.__name__.replace('Controller', '')
        name = re.sub('[A-Z]', lambda x: '_' + x.group().lower(), name).lstrip('_')
        import_name = self.__class__.__module__

        self._blueprint = Blueprint(name, import_name)
        self._register(app)

    @property
    def blueprint(self):
        return self._blueprint

    @property
    def context(self):
        return Context

    @property
    def request(self):
        return Context.request

    @property
    def form(self):
        form = Context.g_get(hard_code.MK_FORM)
        return form

    @property
    def options(self):
        return MetaTable.get(self.__class__, hard_code.MK_OPTIONS, {})

    def _register_methods(self):
        keeps = dir(Controller)
        for k in dir(self):
            if k in keeps:
                continue

            t = getattr(self.__class__, k, None)
            if isinstance(t, property):
                continue

            _f = f = getattr(self, k)
            if callable(f):
                if hasattr(f, '__func__'):
                    f = f.__func__
                meta = MetaTable.all(f)
                if meta is not None:
                    print('  - %s %a' % (f.__qualname__ if hasattr(f, '__qualname__') else f.__name__, meta))
                    self._blueprint.add_url_rule(
                        rule=meta[hard_code.MK_RULE_STR],
                        methods=meta[hard_code.MK_METHODS],
                        view_func=_f
                    )

    def _register(self, app):
        self.callback_before_register()
        print('* Register Controller: %s %a' % (self.__class__, self.options))
        self._register_methods()
        app.register_blueprint(self._blueprint, **self.options)

    def callback_before_register(self):
        pass
