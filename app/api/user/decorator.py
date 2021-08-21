from saika import MetaTable

from .user_api import MK_PUBLIC, MK_ROLES


def ignore_auth(f):
    MetaTable.set(f, MK_PUBLIC, True)
    return f


def role_auth(role):
    def wrapper(f):
        roles = MetaTable.get(f, MK_ROLES, [])  # type: list
        roles.append(role)
        return f

    return wrapper
