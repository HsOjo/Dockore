import os

from saika import Environ
from saika.database.config import FileDBConfig
from saika.decorator import config


@config
class DatabaseConfig(FileDBConfig):
    path = os.path.join(Environ.data_dir, 'db.sqlite')
