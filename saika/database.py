from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session

from . import hard_code
from .config import Config
from .meta_table import MetaTable


def model(cls):
    models = MetaTable.get(hard_code.MI_GLOBAL, hard_code.MK_MODELS, [])  # type: list
    models.append(cls)
    return cls


class Database(SQLAlchemy):
    session: Session


@Config.process
def merge_uri(config):
    db = Config.section(hard_code.CK_DATABASE)
    driver = db['driver'].lower()
    if 'mysql' in driver or 'postgresql' in driver:
        uri = '%(driver)s://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s?charset=%(charset)s' % db
    else:
        uri = '%(driver)s://%(path)s' % db

    config['SQLALCHEMY_DATABASE_URI'] = uri


db = Database()
