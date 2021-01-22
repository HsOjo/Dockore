class Field:
    def __init__(self, name, validators):
        self._name = name
        self._validators = validators
        self._errors = []

    def validate(self, v):
        errors = []
        for validator in self._validators:
            if v is not None or validator.validate_on_none:
                if not validator.validate(v):
                    errors.append(validator.error(self._name))
                    break

        self._errors = errors
        return len(errors) == 0

    @property
    def errors(self):
        return self._errors


class Request:
    def __init__(self, data: dict):
        self._fields = {}
        self._data = data
        self._errors = {}

        for k in dir(self):
            v = getattr(self, k)
            if issubclass(v.__class__, Field):
                self._fields[k] = v

    def validate(self):
        errors = {}
        for k, f in self._fields.items():
            f: Field
            if not f.validate(self._data.get(k)):
                errors[k] = f.errors
        self._errors = errors
        return len(errors) == 0

    @property
    def errors(self):
        return self._errors
