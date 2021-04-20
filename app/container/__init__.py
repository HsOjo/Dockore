from app.user.controller import UserAPIController
from saika.decorator import *
from .enum import *
from .forms import *
from .service import *


@register_controller('/api/container')
class Container(UserAPIController):
    @get
    @rule('/list')
    @form(ListForm)
    def list(self):
        is_all = self.form.is_all.data
        self.success(
            items=ContainerService.list(is_all)
        )

    @get
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
        error = {}

        for id in ids:
            try:
                if ContainerService.delete(id):
                    success.append(id)
                else:
                    error[id] = None
            except Exception as e:
                error[id] = str(e)

        if len(error):
            self.error(*DELETE_FAILED, excs=error)
        else:
            self.success(*DELETE_SUCCESS)

    @post
    @rule('/create')
    @form(CreateForm)
    def create(self):
        try:
            return self.response(*CREATE_SUCCESS, item=ContainerService.create(
                self.form.name.data,
                self.form.image.data,
                self.form.command.data,
            ))
        except Exception as e:
            self.error(*CREATE_FAILED, exc=str(e))
