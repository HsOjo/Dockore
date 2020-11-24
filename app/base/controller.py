import re
from functools import wraps

from flask import Blueprint


class Controller:
    name = None
    import_name = None
    url_prefix = None

    def __init__(self, app):
        if self.name is None:
            self.name = self.__class__.__name__.replace('Controller', '')
            self.name = re.sub('[A-Z]', lambda x: '.' + x.group().lower(), self.name).lstrip('.')

        self._blueprint = Blueprint(self.name, self.import_name)

        self.callback_add_routes()

        if self.url_prefix is None:
            self.url_prefix = '/%s' % self.name.replace('.', '/')
        app.register_blueprint(self._blueprint, url_prefix=self.url_prefix)

    def callback_add_routes(self):
        pass

    def add_route(self, rule, view_func, **kwargs):
        @wraps(view_func)
        def _view_func(*args, **kwargs):
            return self._response_func(view_func, *args, **kwargs)

        self._blueprint.add_url_rule(rule, view_func=_view_func, **kwargs)

    def _response_func(self, view_func, *args, **kwargs):
        return view_func(*args, **kwargs)
