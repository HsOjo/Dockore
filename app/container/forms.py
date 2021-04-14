from wtforms import BooleanField, SelectMultipleField

from saika.form import JSONForm


class ListForm(JSONForm):
    is_all = BooleanField('显示所有', default=False)


class DeleteForm(JSONForm):
    ids = SelectMultipleField('被删除项')
