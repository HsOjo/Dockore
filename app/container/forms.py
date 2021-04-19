from wtforms import BooleanField, StringField
from wtforms.validators import DataRequired

from saika.form import Form, ArgsForm, DataField


class ListForm(ArgsForm):
    is_all = BooleanField('显示所有', default=False)


class DeleteForm(Form):
    ids = DataField('被删除项')


class CreateForm(Form):
    image = StringField('镜像', validators=[DataRequired()])
    command = StringField('命令', validators=[DataRequired()])
    name = StringField('名称')
