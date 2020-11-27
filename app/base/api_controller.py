import sys
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
            tb_msg = traceback.format_exc()
            return jsonify(code=e.code, msg=e.msg or tb_msg)
        except:
            tb_msg = traceback.format_exc()
            print(tb_msg, file=sys.stderr)
            return jsonify(code=APIErrorException.code, msg=tb_msg)

    def make_response(self, code=0, msg='', **data):
        return jsonify(dict(code=code, msg=msg, data=data))

    def hook_before_view(self):
        pass

    def hook_after_view(self):
        pass
