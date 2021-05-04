from saika.form import JSONForm
from wtforms import StringField, FieldList, Field, BooleanField
from wtforms.validators import DataRequired, IPAddress


class OperationForm(JSONForm):
    ids = FieldList(StringField('被操作项', validators=[DataRequired()]))


class ConnectForm(JSONForm):
    id = StringField('网络', validators=[DataRequired()])
    container_id = StringField('被操作容器', validators=[DataRequired()])
    ipv4_address = StringField('IPv4地址', validators=[IPAddress()])


class DisconnectForm(JSONForm):
    id = StringField('网络', validators=[DataRequired()])
    container_id = StringField('被操作容器', validators=[DataRequired()])
    force = BooleanField('强制断开')


class CreateForm(JSONForm):
    name = StringField('名称', validators=[DataRequired()])
    driver = StringField('驱动类型', validators=[DataRequired()])
    attachable = BooleanField('开放连接', validators=[DataRequired()])
    options = Field('选项')
