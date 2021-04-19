from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict
from wtforms import Field

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
        form = cls(**args)  # type: Form
        Context.g_set(hard_code.MK_FORM, form)
        if args.get(hard_code.AK_VALIDATE):
            if not form.validate():
                raise FormException(*PARAMS_MISMATCH)


class DataField(Field):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist


class Form(FlaskForm):
    data: dict
    errors: dict


class ArgsForm(Form):
    def __init__(self, **kwargs):
        super().__init__(MultiDict(Context.request.args), **kwargs)
