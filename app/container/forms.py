from wtforms import BooleanField, StringField
from wtforms.validators import DataRequired

from saika.form import Form, ArgsForm, DataField


class ListForm(ArgsForm):
    is_all = BooleanField('显示所有', default=False)


class OperationForm(Form):
    ids = DataField('被操作项', validators=[DataRequired()])


class CreateForm(Form):
    image = StringField('镜像', validators=[DataRequired()])
    command = StringField('命令', validators=[DataRequired()])
    name = StringField('容器名称')
