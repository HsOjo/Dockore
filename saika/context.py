from flask import request, session, g, current_app


class Context:
    request = request
    session = session
    current_app = current_app

    @staticmethod
    def g_set(k, v):
        setattr(g, k, v)

    @staticmethod
    def g_get(k, default=None):
        return getattr(g, k, default)

    @staticmethod
    def view_function():
        f = current_app.view_functions.get(request.endpoint)
        if hasattr(f, '__func__'):
            f = f.__func__

        return f
