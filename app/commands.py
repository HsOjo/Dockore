def register(manager):
    @manager.command
    def register_user():
        from app.user.service import UserService

        username = input('Input Username: ')
        password = input('Input Password: ')

        try:
            UserService.register(username, password)
            print('Register success.')
        except Exception as e:
            print('Register failed.')
            raise e
