from saika.form import JSONForm, simple_choices, ArgsForm
from wtforms import StringField, IntegerField, SelectField, FieldList
from wtforms.validators import DataRequired

from app.api.user import RoleShip


class ListForm(ArgsForm):
    keyword = StringField('关键字', default='')
    page = IntegerField('页数', default=1)
    per_page = IntegerField('每页项目数', default=10)


class AddForm(JSONForm):
    username = StringField('用户名', validators=[DataRequired()])
    password = StringField('密码')
    role_type = SelectField('角色类型', coerce=int, choices=simple_choices(
        [RoleShip.TYPE_ADMIN, RoleShip.TYPE_USER]
    ))


class EditForm(AddForm):
    id = IntegerField('用户')


class OperationForm(JSONForm):
    ids = FieldList(IntegerField('被操作项', validators=[DataRequired()]))


class DistributeForm(JSONForm):
    id = IntegerField('用户', validators=[DataRequired()])
    type = IntegerField('类型', validators=[DataRequired()])
    obj_id = StringField('对象', validators=[DataRequired()])
