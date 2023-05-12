from saika import Config, Context
from saika.decorator import *
from saika.form import AUTO

from .enums import *
from .forms import *
from ..admin_api import AdminAPIController


@controller
class AdminSystem(AdminAPIController):
    @get
    @post
    @rule('/config')
    @form(ConfigForm, AUTO)
    def config(self):
        if Context.request.method == 'GET':
            self.success(config={k: cfg.data_now for k, cfg in Config.all(True).items()})
        elif Context.request.method == 'POST':
            try:
                configs = Config.all(True)
                save_configs = []
                for k, v in self.form.config.data.items():
                    cfg = configs.get(k)
                    if cfg:
                        cfg.load(**v)
                        save_configs.append(cfg)
                Config.save(*save_configs)
                self.app.load_configs()
            except Exception as e:
                self.error(*CONFIG_FAILED, exc=e)
            self.success(*CONFIG_SUCCESS)
