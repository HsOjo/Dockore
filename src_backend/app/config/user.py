from saika import BaseConfig
from saika.decorator import config


@config
class UserConfig(BaseConfig):
    login_expires = 86400
