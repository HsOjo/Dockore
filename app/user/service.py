import datetime
import hashlib
import time

from app import db
from .models import User, UserToken


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
            token = UserToken(
                user_id=item.id,
                content=pw_hash('%s,%s' % (item.id, time.time())),
                create_time=datetime.datetime.now()
            )
            db.session.add(token)
            db.session.commit()
            return token

    @staticmethod
    def get_user(token: str):
        item = UserToken.query.filter_by(content=token).first()  # type: UserToken
        if item is not None:
            return item.user
        return False
