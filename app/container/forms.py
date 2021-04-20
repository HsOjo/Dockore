from wtforms import BooleanField, StringField, IntegerField, DateTimeField
from wtforms.validators import DataRequired

from saika.form import Form, ArgsForm, DataField


class ListForm(ArgsForm):
    is_all = BooleanField('显示所有', default=False)


class OperationForm(Form):
    ids = DataField('被操作项', validators=[DataRequired()])


class StopForm(OperationForm):
    timeout = IntegerField('超时时间', default=10)


class CreateForm(Form):
    image = StringField('镜像', validators=[DataRequired()])
    command = StringField('命令', validators=[DataRequired()])
    name = StringField('容器名称')
    interactive = BooleanField('交互模式')
    tty = BooleanField('虚拟终端')


class RenameForm(Form):
    id = StringField('容器', validators=[DataRequired()])
    name = StringField('新容器名称', validators=[DataRequired()])


class LogsForm(Form):
    id = StringField('容器', validators=[DataRequired()])
    since = DateTimeField('起始时间')
    until = DateTimeField('终止时间')
