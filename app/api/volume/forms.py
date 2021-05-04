from saika.form import JSONForm
from wtforms import StringField, FieldList, Field
from wtforms.validators import DataRequired


class OperationForm(JSONForm):
    ids = FieldList(StringField('被操作项', validators=[DataRequired()]))


class CreateForm(JSONForm):
    name = StringField('名称', validators=[DataRequired()])
    driver = StringField('驱动器类型', validators=[DataRequired()])
    driver_opts = Field('驱动器选项')
