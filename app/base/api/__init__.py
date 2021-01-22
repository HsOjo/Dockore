import sys
import traceback

from flask import jsonify, request

from .decorator import *
from .enum import *
from .exception import *
from ..controller import Controller
from ..request import Request


class APIController(Controller):
    def _response_func(self, view_func, *args, **kwargs):
        try:
            req_cls = MetaTable.get(view_func.__func__, 'request_class')
            if req_cls is not None:
                req = req_cls(request.get_json())  # type: Request
                if not req.validate():
                    raise APIErrorException(*PARAMS_MISMATCH, data=req.errors)

            return super()._response_func(view_func, *args, **kwargs)
        except APIErrorException as e:
            return self.make_response(e.code, e.msg, **e.data)
        except:
            tb_msg = traceback.format_exc()
            print(tb_msg, file=sys.stderr)
            return self.make_response(*API_ERROR)

    @staticmethod
    def make_response(code=0, msg='', **data):
        return jsonify(dict(code=code, msg=msg, data=data))
