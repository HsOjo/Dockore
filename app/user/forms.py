from wtforms import StringField
from wtforms.validators import DataRequired

from saika.form import JSONForm


class LoginForm(JSONForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = StringField('密码', validators=[DataRequired()])
