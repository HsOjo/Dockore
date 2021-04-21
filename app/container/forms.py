from wtforms import BooleanField, StringField, IntegerField, DateTimeField, FormField, SelectField
from wtforms.validators import DataRequired, NumberRange, IPAddress

from saika.form import Form, ArgsForm, ListField, simple_choices


class ListForm(ArgsForm):
    is_all = BooleanField('显示所有', default=False)


class OperationForm(Form):
    ids = ListField(StringField('被操作项', validators=[DataRequired()]))


class StopForm(OperationForm):
    timeout = IntegerField('超时时间', default=10)


class PortMappintForm(Form):
    port = IntegerField('端口', validators=[DataRequired(), NumberRange(1, 65535)])
    protocol = SelectField('协议', validators=[DataRequired()], choices=simple_choices(['tcp', 'udp', 'sctp']))
    listen_ip = StringField('监听主机', validators=[DataRequired(), IPAddress()])
    listen_port = IntegerField('监听端口', validators=[DataRequired(), NumberRange(1, 65535)])


class CreateForm(Form):
    image = StringField('镜像', validators=[DataRequired()])
    command = StringField('命令', validators=[DataRequired()])
    name = StringField('容器名称')
    interactive = BooleanField('交互模式')
    tty = BooleanField('虚拟终端')
    ports = ListField(FormField(PortMappintForm, '端口映射项'))


class RenameForm(Form):
    id = StringField('容器', validators=[DataRequired()])
    name = StringField('新容器名称', validators=[DataRequired()])


class LogsForm(Form):
    id = StringField('容器', validators=[DataRequired()])
    since = DateTimeField('起始时间')
    until = DateTimeField('终止时间')
