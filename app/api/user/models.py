from datetime import datetime
from typing import List

from saika.database import db
from saika.decorator import model


@model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    username = db.Column(db.VARCHAR(255), unique=True)
    password = db.Column(db.VARCHAR(255))

    role = db.relationship('RoleShip', backref='user', uselist=False, cascade='all')  # type: RoleShip
    own_items = db.relationship('OwnerShip', backref='user', uselist=True, cascade='all')  # type: OwnerShip

    def filter_owner(self, type, items):
        if self.role.type == RoleShip.TYPE_ADMIN:
            return items

        result = []
        owners = db.query(OwnerShip).filter_by(user_id=self.id, type=type).all()  # type: List[OwnerShip]
        if owners:
            mapping = {item['id']: item for item in items}
            for owner in owners:
                item = mapping.get(owner.obj_id)
                if item:
                    result.append(item)

        return result

    def filter_owner_ids(self, type, ids):
        if self.role.type == RoleShip.TYPE_ADMIN:
            return ids

        result = []
        owners = db.query(OwnerShip).filter_by(user_id=self.id, type=type).all()  # type: List[OwnerShip]
        if owners:
            mapping = {id: id for id in ids}
            for owner in owners:
                id = mapping.get(owner.obj_id)
                if id:
                    result.append(id)

        return result

    def check_permission(self, type, obj_id):
        if self.role.type == RoleShip.TYPE_ADMIN:
            return True

        obj = db.query(OwnerShip).filter_by(user_id=self.id, type=type, obj_id=obj_id).first()
        return obj is not None


@model
class RoleShip(db.Model):
    __tablename__ = 'role_ship'

    TYPE_ADMIN = 0
    TYPE_USER = 1

    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    type = db.Column(db.INTEGER, index=True)
    user_id = db.Column(db.INTEGER, db.ForeignKey(User.id), index=True)
    create_time = db.Column(db.DATETIME, default=datetime.now)

    user: User


@model
class OwnerShip(db.Model):
    __tablename__ = 'owner_ship'

    OBJ_TYPE_IMAGE = 1
    OBJ_TYPE_CONTAINER = 2
    OBJ_TYPE_NETWORK = 3
    OBJ_TYPE_VOLUME = 4

    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    type = db.Column(db.INTEGER, index=True)
    user_id = db.Column(db.INTEGER, db.ForeignKey(User.id), index=True)
    obj_id = db.Column(db.VARCHAR(255))
    create_time = db.Column(db.DATETIME, default=datetime.now)

    user: User
