from typing import Dict

from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict
from wtforms import Field
from wtforms.fields.core import UnboundField

from . import hard_code, common
from .context import Context
from .enums import PARAMS_MISMATCH
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
                print(form.errors)
                raise FormException(*PARAMS_MISMATCH, data=dict(
                    errors=common.obj_standard(form.errors, True, True)
                ))


def simple_choices(obj):
    if isinstance(obj, list):
        return [(i, i) for i in obj]
    elif isinstance(obj, dict):
        return [(v, k) for k, v in obj.items()]
    return obj


class ListField(Field):
    def __init__(self, item_field=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._item_fields = {}  # type: Dict[Field]
        self._item_field_g = item_field
        if isinstance(item_field, UnboundField):
            self._item_field_g = lambda: UnboundField(
                item_field.field_class, *item_field.args, **item_field.kwargs
            )
        self._data_md = None
        self._data = None
        self._errors = []

    def process_formdata(self, valuelist):
        if valuelist:
            self._data = valuelist
            self._data_md = MultiDict([(str(i), v) for i, v in enumerate(valuelist)])

            for k, v in self._data_md.items():
                field = self._item_field_g()
                field = field.bind(form=None, name=k, id=k, _meta=self.meta, translations=self._translations)
                field.process(self._data_md, v)
                self._item_fields[k] = field

    def validate(self, *args, **kwargs):
        success = True
        for field in self._item_fields.values():
            if not field.validate(*args, **kwargs):
                success = False
        return success

    @property
    def errors(self):
        return {int(k): f.errors for k, f in self._item_fields.items() if f.errors}

    @property
    def data(self):
        return [f.data for f in self._item_fields.values()]

    @data.setter
    def data(self, v):
        self._data = v


class Form(FlaskForm):
    data: dict
    errors: dict


class ArgsForm(Form):
    def __init__(self, **kwargs):
        super().__init__(MultiDict(Context.request.args), **kwargs)
