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
    @form(OperationForm)
    def delete(self):
        ids = self.form.ids.data

        excs = {}

        for id in ids:
            try:
                ContainerService.delete(id)
            except Exception as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*DELETE_FAILED, excs=excs)

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

    @post
    @rule('/start')
    @form(OperationForm)
    def start(self):
        ids = self.form.ids.data

        excs = {}
        for id in ids:
            try:
                ContainerService.start(id)
            except Exception as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*START_FAILED, excs=excs)

        self.success(*START_SUCCESS)

    @post
    @rule('/stop')
    @form(OperationForm)
    def stop(self):
        ids = self.form.ids.data

        excs = {}
        for id in ids:
            try:
                ContainerService.stop(id)
            except Exception as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*STOP_FAILED, excs=excs)

        self.success(*STOP_SUCCESS)

    @post
    @rule('/restart')
    @form(OperationForm)
    def restart(self):
        ids = self.form.ids.data

        excs = {}
        for id in ids:
            try:
                ContainerService.restart(id)
            except Exception as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*RESTART_FAILED, excs=excs)

        self.success(*RESTART_SUCCESS)
