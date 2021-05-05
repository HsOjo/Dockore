from saika import SaikaApp, set_form_validate_default, set_fork_killer


class Application(SaikaApp):
    def callback_init_app(self):
        set_form_validate_default(True)
        set_fork_killer(False)


app = Application()
