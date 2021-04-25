from saika.form import JSONForm, ArgsForm
from wtforms import BooleanField, StringField, FieldList
from wtforms.validators import DataRequired


class ListForm(ArgsForm):
    is_all = BooleanField('显示所有', default=False)


class OperationForm(JSONForm):
    ids = FieldList(StringField('被操作项', validators=[DataRequired()]))


class DeleteForm(OperationForm):
    tag_only = BooleanField('仅删除标签')


class PullForm(JSONForm):
    name = StringField('镜像名称', validators=[DataRequired()])
    tag = StringField('版本标签')


class TagForm(JSONForm):
    id = StringField('镜像', validators=[DataRequired()])
    name = StringField('镜像名称', validators=[DataRequired()])
    tag = StringField('版本标签')
