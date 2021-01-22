import re
from functools import wraps

from flask import Blueprint

from ..meta import MetaTable


class Controller:
    name = None
    import_name = None
    url_prefix = None

    def __init__(self, app):
        if self.name is None:
            self.name = self.__class__.__name__.replace('Controller', '')
            self.name = re.sub('[A-Z]', lambda x: '.' + x.group().lower(), self.name).lstrip('.')

        self._blueprint = Blueprint(self.name, self.import_name)
        self._add_routes()

        if self.url_prefix is None:
            self.url_prefix = '/%s' % self.name.replace('.', '/')
        app.register_blueprint(self._blueprint, url_prefix=self.url_prefix)

    def _add_routes(self):
        for k in dir(self):
            f = getattr(self, k)
            if callable(f) and hasattr(f, '__func__'):
                meta = MetaTable.all(f.__func__)
                if meta is not None:
                    self.add_route(meta['rule'], f, methods=meta['methods'])

    def add_route(self, rule, view_func, **kwargs):
        @wraps(view_func)
        def _view_func(*args, **kwargs):
            return self._response_func(view_func, *args, **kwargs)

        self._blueprint.add_url_rule(rule, view_func=_view_func, **kwargs)

    def _response_func(self, view_func, *args, **kwargs):
        self.hook_before_view()
        resp = view_func(*args, **kwargs)
        return self.hook_after_view(resp)

    def hook_before_view(self):
        pass

    def hook_after_view(self, resp):
        return resp
