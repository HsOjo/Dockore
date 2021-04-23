import hashlib

from saika import db, common, Config

from .models import User


def pw_hash(x: str):
    return hashlib.md5(x.encode()).hexdigest()


class UserService:
    @staticmethod
    def register(username, password):
        password = pw_hash(password)
        item = User(
            username=username,
            password=password,
        )
        db.session.add(item)
        db.session.commit()

    @staticmethod
    def login(username, password):
        password = pw_hash(password)
        item = User.query.filter_by(
            username=username,
            password=password,
        ).first()  # type: User

        if item is None:
            return False
        else:
            expires = Config.section('user').get('login_expires', 86400)
            return common.obj_encrypt(dict(id=item.id), expires)

    @staticmethod
    def change_password(username, old, new):
        password = pw_hash(old)
        item = User.query.filter_by(
            username=username,
            password=password,
        ).first()  # type: User

        if item is None:
            return False
        else:
            item.password = pw_hash(new)
            db.session.add(item)
            db.session.commit()
            return True

    @staticmethod
    def get_user(token: str):
        obj = common.obj_decrypt(token)  # type: dict
        if obj is not None:
            id = obj.get('id')
            if id is not None:
                item = User.query.get(id)  # type: User
                if item is not None:
                    return item

        return None
