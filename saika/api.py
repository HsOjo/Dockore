import json

from werkzeug.exceptions import HTTPException

from saika.controller import Controller


class APIException(HTTPException):
    def __init__(self, error_code, msg, data, code):
        super().__init__(msg, None)
        self.error_code = error_code
        self.msg = msg
        self.data = data
        self.code = code

    def get_body(self, environ=None):
        return json.dumps(dict(
            code=self.error_code,
            msg=self.msg,
            data=self.data,
        ))


class APIController(Controller):
    def success(self, code=0, msg=None, **data):
        raise APIException(code, msg, data, 200)

    def error(self, code=1, msg=None, **data):
        raise APIException(code, msg, data, 500)
