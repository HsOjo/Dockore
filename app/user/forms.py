from saika.form import Form
from wtforms import StringField
from wtforms.validators import DataRequired


class LoginForm(Form):
    username = StringField('用户名', validators=[DataRequired()])
    password = StringField('密码', validators=[DataRequired()])


class ChangePasswordForm(Form):
    username = StringField('用户名', validators=[DataRequired()])
    old = StringField('旧密码', validators=[DataRequired()])
    new = StringField('新密码', validators=[DataRequired()])
