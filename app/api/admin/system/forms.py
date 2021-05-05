from saika.form import JSONForm, Form
from wtforms import StringField, IntegerField, FormField
from wtforms.validators import DataRequired


class ConfigForm(JSONForm):
    class _(Form):
        class DatabaseForm(Form):
            driver = StringField('数据库驱动', validators=[DataRequired()])
            host = StringField('主机', validators=[DataRequired()])
            port = IntegerField('端口', validators=[DataRequired()])
            user = StringField('用户', validators=[DataRequired()])
            password = StringField('密码', default='')
            database = StringField('数据库', validators=[DataRequired()])
            charset = StringField('编码', validators=[DataRequired()])

        class DockerForm(Form):
            url = StringField('URL', validators=[DataRequired()])
            cli_bin = StringField('客户端路径', validators=[DataRequired()])
            terminal_expires = IntegerField('交互会话有效期', validators=[DataRequired()])

        class UserForm(Form):
            login_expires = IntegerField('登录过期时间', validators=[DataRequired()])

        database = FormField(DatabaseForm)
        docker = FormField(DockerForm)
        user = FormField(UserForm)

    config = FormField(_)
