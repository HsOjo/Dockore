import re

from flask import Blueprint

from . import hard_code
from .context import Context
from .meta_table import MetaTable


class Controller:
    def __init__(self):
        name = self.__class__.__name__.replace('Controller', '')
        name = re.sub('[A-Z]', lambda x: '_' + x.group().lower(), name).lstrip('_')
        import_name = self.__class__.__module__

        self._blueprint = Blueprint(name, import_name)

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

    def _register_methods(self):
        keeps = dir(Controller)
        for k in dir(self):
            if k in keeps:
                continue

            t = getattr(self.__class__, k, None)
            if isinstance(t, property):
                continue

            f = getattr(self, k)
            if callable(f) and hasattr(f, '__func__'):
                meta = MetaTable.all(f.__func__)
                if meta is not None:
                    print('Register method: %s (%a)' % (f, meta))
                    self._blueprint.add_url_rule(
                        rule=meta[hard_code.MK_RULE_STR],
                        methods=meta[hard_code.MK_METHODS],
                        view_func=f
                    )

    def register(self, app):
        options = MetaTable.get(self.__class__, hard_code.MK_OPTIONS, {})
        print('Register controller: %s (%a)' % (self.__class__, options))

        self.callback_before_register()
        self._register_methods()
        app.register_blueprint(self._blueprint, **options)

    def callback_before_register(self):
        pass
