from app.user.controller import UserAPIController
from saika.decorator import *
from .enum import *
from .forms import *
from .service import *


@register_controller('/api/image')
class Image(UserAPIController):
    @get
    @rule('/list')
    @form(ListForm)
    def list(self):
        is_all = self.form.is_all.data

        self.success(
            items=ImageService.list(is_all)
        )

    @get
    @rule('/item/<string:id>')
    def item(self, id):
        self.success(
            item=ImageService.item(id)
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
                ImageService.delete(id)
                success.append(id)
            except Exception as e:
                error[id] = str(e)

        if len(error):
            self.error(*DELETE_FAILED, excs=error)
        else:
            self.success(*DELETE_SUCCESS)

    @get
    @rule('/search/<string:keyword>')
    def search(self, keyword):
        self.success(
            items=ImageService.search(keyword)
        )

    @post
    @rule('/pull')
    @form(PullForm)
    def pull(self):
        try:
            return self.response(
                *PULL_SUCCESS, item=ImageService.pull(
                    self.form.name.data,
                    self.form.tag.data,
                ))
        except Exception as e:
            self.error(*PULL_FAILED, exc=str(e))
