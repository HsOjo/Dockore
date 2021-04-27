from saika.database import db
from saika.decorator import model


@model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    username = db.Column(db.VARCHAR(255), unique=True)
    password = db.Column(db.VARCHAR(255))
