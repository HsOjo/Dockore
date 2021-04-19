from wtforms import BooleanField

from saika.form import Form, ArgsForm, DataField


class ListForm(ArgsForm):
    is_all = BooleanField('显示所有', default=False)


class DeleteForm(Form):
    ids = DataField('被删除项')
