from flask_cors import CORS

from saika import SaikaApp


class Application(SaikaApp):
    def callback_init_app(self):
        cors.init_app(self)


cors = CORS(supports_credentials=True)
app = Application()
