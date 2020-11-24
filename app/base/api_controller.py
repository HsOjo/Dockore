import traceback

from flask import jsonify

from .controller import Controller


class APIErrorException(Exception):
    code = -1
    msg = '服务器错误，请联系管理员进行处理。'


class APIController(Controller):
    class ParamsNotMatchException(APIErrorException):
        code = -2
        msg = 'API调用参数错误。'

    def _response_func(self, view_func, *args, **kwargs):
        try:
            self.hook_before_view()
            resp = view_func(*args, **kwargs)
            self.hook_after_view()
            return resp
        except APIErrorException as e:
            return jsonify(error=e.code, msg=e.msg, exc=traceback.format_exc())
        except:
            return jsonify(error=APIErrorException.code, exc=traceback.format_exc())

    def make_response(self, error=0, **data):
        return jsonify(dict(error=error, data=data))

    def hook_before_view(self):
        pass

    def hook_after_view(self):
        pass
