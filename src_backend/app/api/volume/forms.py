from saika.form import JSONForm
from wtforms import StringField, FieldList, FormField, Form
from wtforms.validators import DataRequired


class OperationForm(JSONForm):
    ids = FieldList(StringField('被操作项', validators=[DataRequired()]))


class CreateForm(JSONForm):
    class DriverOptionForm(Form):
        key = StringField('键', validators=[DataRequired()])
        value = StringField('值', validators=[DataRequired()])

    name = StringField('名称', validators=[DataRequired()])
    driver = StringField('驱动器类型', validators=[DataRequired()])
    driver_opts = FieldList(FormField(DriverOptionForm, '驱动器选项'))
