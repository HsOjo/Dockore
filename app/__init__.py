from saika import SaikaApp
from saika.form import set_default_validate


class Application(SaikaApp):
    def callback_init_app(self):
        set_default_validate(True)


app = Application()
