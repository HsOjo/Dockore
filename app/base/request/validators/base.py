class ValidatorBase:
    validate_on_none = False

    def validate(self, v) -> bool:
        pass

    def error(self, name) -> str:
        pass
