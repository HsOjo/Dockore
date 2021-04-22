from flask import render_template

from . import hard_code
from .controller import Controller


class ViewControlller(Controller):
    def assign(self, **kwargs):
        context = self.context.g_get(hard_code.GK_CONTEXT)
        if context is None:
            context = {}
            self.context.g_set(hard_code.GK_CONTEXT, context)
        context.update(kwargs)

    def fetch(self, template):
        context = self.context.g_get(hard_code.GK_CONTEXT, {})
        return render_template(template, **context)
