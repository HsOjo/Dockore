from .base import ValidatorBase


class Required(ValidatorBase):
    validate_on_none = True

    def validate(self, v) -> bool:
        return v is not None

    def error(self, name) -> str:
        return '"%s"为必填项。' % name


class DataRequired(ValidatorBase):
    validate_on_none = True

    def validate(self, v) -> bool:
        return v is not None and v != '' and v != 0

    def error(self, name) -> str:
        return '''"%s"不能为空白。''' % name


class TypeCheck(ValidatorBase):
    def __init__(self, type_):
        self._type = type_

    def validate(self, v) -> bool:
        return isinstance(v, self._type)

    def error(self, name) -> str:
        return '''"%s"必须为"%s"类型。''' % (name, self._type.__name__)


class RangeCheck(ValidatorBase):
    def __init__(self, min_, max_):
        self.min_ = min_
        self.max_ = max_

    def validate(self, v) -> bool:
        return self.min_ <= v <= self.max_

    def error(self, name) -> str:
        return '''"%s"必须在范围%s-%s内。''' % (name, self.min_, self.max_)
