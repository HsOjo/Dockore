import os

from itsdangerous import TimedJSONWebSignatureSerializer

from .environ import Environ


def get_program_path():
    app_path = Environ.app.root_path  # type: str
    path = os.path.join(app_path, '..')
    return path


def obj_encrypt(obj, expires_in=None):
    return TimedJSONWebSignatureSerializer(Environ.app.secret_key, expires_in).dumps(obj).decode()


def obj_decrypt(obj_str):
    try:
        return TimedJSONWebSignatureSerializer(Environ.app.secret_key).loads(obj_str)
    except:
        return None
