from saika.form import JSONForm
from wtforms import StringField, FieldList, BooleanField, FormField, Form
from wtforms.validators import DataRequired


class OperationForm(JSONForm):
    ids = FieldList(StringField('被操作项', validators=[DataRequired()]))


class ConnectForm(JSONForm):
    id = StringField('网络', validators=[DataRequired()])
    container_id = StringField('被操作容器', validators=[DataRequired()])
    ipv4_address = StringField('IPv4地址')


class DisconnectForm(JSONForm):
    id = StringField('网络', validators=[DataRequired()])
    container_id = StringField('被操作容器', validators=[DataRequired()])
    force = BooleanField('强制断开')


class CreateForm(JSONForm):
    class OptionForm(Form):
        key = StringField('键', validators=[DataRequired()])
        value = StringField('值', validators=[DataRequired()])

    name = StringField('名称', validators=[DataRequired()])
    driver = StringField('驱动类型', validators=[DataRequired()])
    attachable = BooleanField('开放连接', default=True)
    options = FieldList(FormField(OptionForm, '选项'))
    subnet = StringField('子网网段')
    gateway = StringField('网关')
    ip_range = StringField('IP范围')
