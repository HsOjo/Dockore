from app.base.meta import MetaTable


def request_check(cls):
    def wrapper(f):
        MetaTable.set(f, 'request_class', cls)
        return f

    return wrapper
