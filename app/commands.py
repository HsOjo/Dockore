from app.api.user import RoleShip


def register(manager):
    def useradd():
        from app.api.admin.user import AdminUserService

        username = input('Input Username: ')
        password = input('Input Password: ')
        is_admin = input('Is Admin? (Y/n): ').lower() != 'n'

        try:
            role_type = RoleShip.TYPE_ADMIN if is_admin else RoleShip.TYPE_USER
            AdminUserService.add(username, password, role_type)
            print('Register success.')
        except Exception as e:
            print('Register failed.')
            raise e

    useradd.__doc__ = 'Add a user for dockore by command.'
    manager.command(useradd)
