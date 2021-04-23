from docker.errors import APIError
from saika.decorator import *

from app.base.controller import DockerAPIController
from .enums import *
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
    @form(DeleteForm)
    def delete(self):
        ids = self.form.ids.data
        tag_only = self.form.tag_only.data

        excs = {}

        for id in ids:
            try:
                self.docker.image.remove(id, tag_only)
            except APIError as e:
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
                    **self.form.data
                ))
        except APIError as e:
            self.error(*PULL_FAILED, exc=str(e))

    @post
    @rule('/tag')
    @form(TagForm)
    def tag(self):
        if self.docker.image.tag(**self.form.data):
            self.success(*TAG_SUCCESS)
        else:
            self.error(*TAG_FAILED)

    @get
    @rule('/history/<string:id>')
    def history(self, id):
        self.success(
            histories=self.docker.image.history(id)
        )
