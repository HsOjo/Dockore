from saika import SaikaApp


class Application(SaikaApp):
    def callback_init_app(self):
        self.set_form_validate_default(True)
        self.set_fork_killer(False)


app = Application()
