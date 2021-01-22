from app.base.api import Request
from app.base.request import Field
from app.base.request.validators import DataRequired, TypeCheck


class LoginRequest(Request):
    username = Field('用户名', validators=[DataRequired(), TypeCheck(str)])
    password = Field('密码', validators=[DataRequired(), TypeCheck(str)])
