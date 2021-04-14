from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict

from . import hard_code
from .context import Context
from .enum import PARAMS_MISMATCH
from .environ import Environ
from .exception import AppException
from .meta_table import MetaTable


class FormException(AppException):
    pass


@Environ.app.before_request
def process_form():
    if Context.request.method == 'OPTIONS':
        return

    f = Context.view_function()
    cls = MetaTable.get(f, hard_code.MK_FORM_CLASS)
    if cls is not None:
        args = MetaTable.get(f, hard_code.MK_FORM_ARGS)
        form = cls(**args)  # type: BaseForm
        Context.g_set(hard_code.MK_FORM, form)
        if args.get('validate'):
            if not form.validate():
                raise FormException(*PARAMS_MISMATCH)


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
