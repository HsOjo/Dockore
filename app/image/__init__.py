from app.base.controller import DockerAPIController
from saika.decorator import *
from .enum import *
from .forms import *


@register_controller('/api/image')
class Image(DockerAPIController):
    @get
    @rule('/list')
    @form(ListForm)
    def list(self):
        self.success(
            items=self.docker.image.list(all=self.form.is_all.data)
        )

    @get
    @rule('/item/<string:id>')
    def item(self, id):
        self.success(
            item=self.docker.image.item(id)
        )

    @post
    @rule('/delete')
    @form(OperationForm)
    def delete(self):
        ids = self.form.ids.data

        excs = {}

        for id in ids:
            try:
                self.docker.image.remove(id)
            except Exception as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*DELETE_FAILED, excs=excs)

        self.success(*DELETE_SUCCESS)

    @get
    @rule('/search/<string:keyword>')
    def search(self, keyword):
        self.success(
            items=self.docker.image.search(keyword)
        )

    @post
    @rule('/pull')
    @form(PullForm)
    def pull(self):
        try:
            return self.response(
                *PULL_SUCCESS, item=self.docker.image.pull(
                    self.form.name.data,
                    self.form.tag.data,
                ))
        except Exception as e:
            self.error(*PULL_FAILED, exc=str(e))
