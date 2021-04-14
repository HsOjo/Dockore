import json

from .controller import Controller
from .exception import AppException


class APIException(AppException):
    def get_body(self, environ=None):
        return json.dumps(dict(
            code=self.error_code,
            msg=self.msg,
            data=self.data,
        ))


class APIController(Controller):
    def callback_before_register(self):
        @self.blueprint.errorhandler(AppException)
        def _process_exception(e: AppException):
            return APIException(e.error_code, e.msg, e.data, e.code)

    def success(self, code=0, msg=None, **data):
        raise APIException(code, msg, data, 200)

    def error(self, code=1, msg=None, **data):
        raise APIException(code, msg, data, 500)
