from . import hard_code
from .meta_table import MetaTable


def rule(rule_str):
    def wrapper(f):
        MetaTable.set(f, hard_code.MK_RULE_STR, rule_str)
        return f

    return wrapper


def register_controller(url_prefix, **options):
    opts = locals().copy()
    opts.update(opts.pop('options'))

    def wrapper(cls):
        controllers = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_CONTROLLER_CLASSES, [])  # type: list
        controllers.append(cls)
        MetaTable.set(cls, hard_code.MK_OPTIONS, opts)
        return cls

    return wrapper


def form(form_cls, validate=True, **kwargs):
    kwargs['validate'] = validate

    def wrapper(f):
        MetaTable.set(f, hard_code.MK_FORM_CLASS, form_cls)
        MetaTable.set(f, hard_code.MK_FORM_ARGS, kwargs)
        return f

    return wrapper


def _method(f, method):
    methods = MetaTable.get(f, hard_code.MK_METHODS, [])  # type: list
    methods.append(method)
    return f


get = lambda f: _method(f, 'GET')
post = lambda f: _method(f, 'POST')
