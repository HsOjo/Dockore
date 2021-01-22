from ..meta import MetaTable


def mapping_rule(rule):
    def wrapper(f):
        MetaTable.set(f, 'rule', rule)
        return f

    return wrapper


def post(f):
    options = MetaTable.get(f, 'methods', [])  # type: list
    options.append('POST')
    return f


def get(f):
    options = MetaTable.get(f, 'methods', [])  # type: list
    options.append('GET')
    return f
