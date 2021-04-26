from saika.form import JSONForm
from wtforms import StringField
from wtforms.validators import DataRequired


class LoginForm(JSONForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = StringField('密码', validators=[DataRequired()])


class ChangePasswordForm(JSONForm):
    old = StringField('旧密码', validators=[DataRequired()])
    new = StringField('新密码', validators=[DataRequired()])
