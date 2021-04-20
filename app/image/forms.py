from wtforms import BooleanField, StringField
from wtforms.validators import DataRequired

from saika.form import Form, ArgsForm, DataField


class ListForm(ArgsForm):
    is_all = BooleanField('显示所有', default=False)


class OperationForm(Form):
    ids = DataField('被操作项', validators=[DataRequired()])


class PullForm(Form):
    name = StringField('镜像名称', validators=[DataRequired()])
    tag = StringField('版本标签')


class TagForm(Form):
    id = StringField('镜像', validators=[DataRequired()])
    name = StringField('镜像名称', validators=[DataRequired()])
    tag = StringField('版本标签')

