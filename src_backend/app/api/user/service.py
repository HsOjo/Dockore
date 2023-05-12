import hashlib

from saika import db, common, Service, Config

from app.config.user import UserConfig
from .models import User

EXPIRES_CFG = object()


class UserService(Service):
    def __init__(self):
        super().__init__(User)

    @staticmethod
    def pw_hash(x: str):
        return hashlib.md5(x.encode()).hexdigest()

    def login(self, username, password, expires=EXPIRES_CFG):
        password = self.pw_hash(password)
        item = self.query.filter_by(
            username=username,
            password=password,
        ).first()  # type: User

        if item is None:
            return False
        else:
            if expires is EXPIRES_CFG:
                cfg = Config.get(UserConfig)  # type: UserConfig
                expires = cfg.login_expires
            return common.obj_encrypt(dict(id=item.id), expires)

    def change_password(self, username, old, new):
        password = self.pw_hash(old)
        item = self.query.filter_by(
            username=username,
            password=password,
        ).first()  # type: User

        if item is None:
            return False
        else:
            item.password = self.pw_hash(new)
            db.add_instance(item)
            return True

    def get_user(self, token: str):
        obj = common.obj_decrypt(token)  # type: dict
        if obj is not None:
            id = obj.get('id')
            if id is not None:
                item = self.query.get(id)  # type: User
                if item is not None:
                    return item

        return None
