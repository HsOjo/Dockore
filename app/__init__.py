from flask_cors import CORS
from flask_migrate import Migrate

from saika import SaikaApp, db


class Application(SaikaApp):
    def callback_init_app(self):
        cors.init_app(self)


cors = CORS(supports_credentials=True)
app = Application()
migrate = Migrate(app, db)
