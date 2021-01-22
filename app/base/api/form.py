from flask import request
from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict

from .enum import PARAMS_MISMATCH
from .exception import APIErrorException


class APIForm(FlaskForm):
    def __init__(self, **kwargs):
        super().__init__(MultiDict(request.get_json()), **kwargs)

    def validate_throw_errors(self):
        if not self.validate():
            raise APIErrorException(*PARAMS_MISMATCH, self.errors)
