from werkzeug.exceptions import HTTPException

from .enums import APP_ERROR


class AppException(HTTPException):
    def __init__(self, error_code=APP_ERROR[0], msg=APP_ERROR[1], data=None, code=500):
        super().__init__(msg, None)
        self.error_code = error_code
        self.msg = msg
        self.data = data
        self.code = code
