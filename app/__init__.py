from saika import SaikaApp
from saika.form import set_form_validate_default
from saika.workers import set_fork_killer


class Application(SaikaApp):
    program_rel_path = '..'
    app_module = 'app'

    def callback_init_app(self):
        set_form_validate_default(True)
        set_fork_killer(False)


app = Application()
