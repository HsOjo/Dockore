from app import db


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    username = db.Column(db.VARCHAR(255), unique=True)
    password = db.Column(db.VARCHAR(255))


class UserToken(db.Model):
    __tablename__ = 'user_token'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    user_id = db.Column(db.INTEGER, db.ForeignKey(User.id), index=True)
    content = db.Column(db.VARCHAR(255), unique=True)
    create_time = db.Column(db.DATETIME)

    user = db.relationship(User, uselist=False)  # type: User
