from saika.form import Form
from wtforms import StringField
from wtforms.validators import DataRequired


class LoginForm(Form):
    username = StringField('用户名', validators=[DataRequired()])
    password = StringField('密码', validators=[DataRequired()])
