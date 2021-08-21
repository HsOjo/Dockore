from saika import db

from app.api.user.models import User, RoleShip, OwnerShip
from app.api.user.service import UserService


class AdminUserService(UserService):
    def add(self, username, password, role_type):
        password = self.pw_hash(password)
        return super().add(
            username=username, password=password,
            role=RoleShip(type=role_type)
        )

    def edit(self, id, username=None, password=None, role_type=None, **kwargs):
        item = self.query.get(id)  # type: User
        if not item:
            return False

        item.username = username
        if password:
            password = self.pw_hash(password)
            item.password = password
        item.role.type = role_type
        db.add_instance(item)

    def remove_owner_ship(self, id):
        item = db.query(OwnerShip).get(id)
        db.delete_instance(item)

    def distribute_obj(self, id, type, obj_id):
        fields = dict(user_id=id, type=type, obj_id=obj_id)
        existed = db.query(OwnerShip).filter_by(**fields).first()
        if not existed:
            db.add_instance(OwnerShip(**fields))
            return True

        return False

    def count_admin(self):
        return db.query(RoleShip).filter_by(type=RoleShip.TYPE_ADMIN).count()
