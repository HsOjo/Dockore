from app.base.api import Request
from app.base.request import Field
from app.base.request.validators import TypeCheck


class ListRequest(Request):
    is_all = Field('显示所有', validators=[TypeCheck(bool)])


class DeleteRequest(Request):
    ids = Field('被删除的id', validators=[TypeCheck(list)])
