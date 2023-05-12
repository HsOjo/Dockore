from saika.form import JSONForm, ArgsForm, simple_choices
from wtforms import BooleanField, StringField, IntegerField, DateTimeField, FormField, SelectField, FieldList, Form
from wtforms.validators import DataRequired, NumberRange, IPAddress


class ListForm(ArgsForm):
    is_all = BooleanField('显示所有', default=False)


class OperationForm(JSONForm):
    ids = FieldList(StringField('被操作项', validators=[DataRequired()]))


class StopForm(OperationForm):
    timeout = IntegerField('超时时间', default=10)


class CreateForm(JSONForm):
    class PortMappingForm(Form):
        port = IntegerField('端口', validators=[DataRequired(), NumberRange(1, 65535)])
        protocol = SelectField('协议', validators=[DataRequired()], choices=simple_choices(['tcp', 'udp', 'sctp']))
        listen_ip = StringField('监听主机', validators=[DataRequired(), IPAddress()])
        listen_port = IntegerField('监听端口', validators=[DataRequired(), NumberRange(1, 65535)])

    class VolumeMappingForm(Form):
        path = StringField('存储卷', validators=[DataRequired()])
        mode = SelectField('挂载模式', choices=simple_choices(['ro', 'rw']))
        bind = StringField('挂载位置', validators=[DataRequired()])

    image = StringField('镜像', validators=[DataRequired()])
    command = StringField('命令', validators=[DataRequired()])
    name = StringField('容器名称')
    interactive = BooleanField('交互模式')
    tty = BooleanField('虚拟终端')
    ports = FieldList(FormField(PortMappingForm, '端口映射项'))
    volumes = FieldList(FormField(VolumeMappingForm, '存储卷挂载项'))


class RenameForm(JSONForm):
    id = StringField('容器', validators=[DataRequired()])
    name = StringField('新容器名称', validators=[DataRequired()])


class LogsForm(JSONForm):
    id = StringField('容器', validators=[DataRequired()])
    since = DateTimeField('起始时间')
    until = DateTimeField('终止时间')


class CommitForm(JSONForm):
    id = StringField('容器', validators=[DataRequired()])
    name = StringField('镜像名称', validators=[DataRequired()])
    tag = StringField('版本标签')
    message = StringField('改动消息')
    author = StringField('作者名称')


class TerminalForm(JSONForm):
    id = StringField('容器', validators=[DataRequired()])
    command = StringField('命令')


class ExecForm(TerminalForm):
    interactive = BooleanField('交互模式', default=True)
    tty = BooleanField('虚拟终端', default=True)
    privileged = BooleanField('权限模式', default=False)
    binary = BooleanField('二进制输出', default=False)
