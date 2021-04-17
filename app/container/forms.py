from wtforms import BooleanField, SelectMultipleField, StringField
from wtforms.validators import DataRequired

from saika.form import JSONForm


class ListForm(JSONForm):
    is_all = BooleanField('显示所有', default=False)


class DeleteForm(JSONForm):
    ids = SelectMultipleField('被删除项')


class CreateForm(JSONForm):
    image = StringField('镜像', validators=[DataRequired()])
    command = StringField('命令', validators=[DataRequired()])
    name = StringField('名称')
