from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict

from . import hard_code
from .context import Context
from .environ import Environ
from .meta_table import MetaTable


@Environ.app.before_request
def process_form():
    f = Context.current_app.view_functions[Context.request.endpoint]
    if hasattr(f, '__func__'):
        f = f.__func__
    cls = MetaTable.get(f, hard_code.MK_FORM_CLASS)
    if cls is not None:
        args = MetaTable.get(f, hard_code.MK_FORM_ARGS)
        Context.g_set(hard_code.MK_FORM, cls(**args))


class BaseForm(FlaskForm):
    data: dict
    errors: dict

    def __init__(self, formdata: dict, **kwargs):
        super().__init__(MultiDict(formdata), **kwargs)


class ArgsForm(BaseForm):
    def __init__(self, **kwargs):
        super().__init__(Context.request.args, **kwargs)


class DataForm(BaseForm):
    def __init__(self, **kwargs):
        super().__init__(Context.request.form, **kwargs)


class JSONForm(BaseForm):
    def __init__(self, **kwargs):
        super().__init__(Context.request.get_json(), **kwargs)
