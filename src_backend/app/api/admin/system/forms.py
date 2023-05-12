from saika.form import JSONForm, Form
from wtforms import StringField, IntegerField, FormField, BooleanField, Field
from wtforms.validators import DataRequired


class ConfigForm(JSONForm):
    class _(Form):
        class DatabaseForm(Form):
            driver = StringField('数据库驱动', validators=[DataRequired()])
            path = StringField('文件路径', validators=[DataRequired()])
            echo_sql = BooleanField('输出SQL')
            track_modifications = BooleanField('追踪变化')

        class DockerForm(Form):
            url = StringField('URL', validators=[DataRequired()])
            cli_bin = StringField('客户端路径', validators=[DataRequired()])
            terminal_expires = IntegerField('交互会话有效期', validators=[DataRequired()])

        class UserForm(Form):
            login_expires = IntegerField('登录过期时间', validators=[DataRequired()])

        flask = Field()
        database = FormField(DatabaseForm)
        docker = FormField(DockerForm)
        user = FormField(UserForm)

    config = FormField(_)
