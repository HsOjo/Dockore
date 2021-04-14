from app.user.controller import UserAPIController
from saika.decorator import *
from .enum import *
from .forms import *
from .service import *


@controller('/api/container')
class Container(UserAPIController):
    @post
    @rule('/list')
    @form(ListForm)
    def list(self):
        is_all = self.form.is_all.data
        self.success(
            items=ContainerService.list(is_all)
        )

    @post
    @rule('/item/<string:id>')
    def item(self, id: str):
        self.success(
            item=ContainerService.item(id)
        )

    @post
    @rule('/delete')
    @form(DeleteForm)
    def delete(self):
        ids = self.form.ids.data

        success = []
        error = []

        for id in ids:
            if ContainerService.delete(id):
                success.append(id)
            else:
                error.append(id)

        if len(error):
            self.error(*DELETE_FAILED, error)
        else:
            self.success(*DELETE_SUCCESS)
