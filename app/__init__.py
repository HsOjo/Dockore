from flask_cors import CORS

from saika import SaikaApp
from saika.form import set_default_validate


class Application(SaikaApp):
    def callback_init_app(self):
        set_default_validate(True)

        cors.init_app(self)


cors = CORS(supports_credentials=True)
app = Application()
