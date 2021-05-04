from saika import db

from app.api.user.models import User, RoleShip
from app.api.user.service import pw_hash


class AdminUserService:
    @staticmethod
    def list(page, per_page, keyword=None):
        query = db.query(User)
        if keyword:
            query = query.filter(User.username.contains(keyword))
        return query.paginate(page, per_page)

    @staticmethod
    def item(id):
        return db.query(User).get(id)

    @staticmethod
    def add(username, password, role_type):
        password = pw_hash(password)
        db.add_instance(User(
            username=username, password=password,
            role=RoleShip(type=role_type)
        ))

    @staticmethod
    def edit(id, username, password, role_type):
        item = db.query(User).get(id)  # type: User
        if not item:
            return False

        item.username = username
        if password:
            password = pw_hash(password)
            item.password = password
        item.role.type = role_type
        db.add_instance(item)

    @staticmethod
    def delete(id):
        item = db.query(User).get(id)
        db.delete_instance(item)

    @staticmethod
    def count_admin():
        return db.query(RoleShip).filter_by(type=RoleShip.TYPE_ADMIN).count()
