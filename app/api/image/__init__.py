from docker.errors import APIError
from saika import db
from saika.decorator import *

from app.api.base import DockerAPIController
from .enums import *
from .forms import *
from ..enums import OBJECT_NOT_EXISTED
from ..user import ROLE_PERMISSION_DENIED
from ..user.models import OwnerShip, RoleShip


@controller()
class Image(DockerAPIController):
    @get
    @rule('/list')
    @form(ListForm)
    def list(self):
        items = self.docker.image.list(all=self.form.is_all.data)
        items = self.current_user.filter_owner(OwnerShip.OBJ_TYPE_IMAGE, items)
        self.success(items=items)

    @get
    @rule('/item/<string:id>')
    def item(self, id):
        item = self.docker.image.item(id)
        if not item:
            self.error(*OBJECT_NOT_EXISTED)
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_IMAGE, item['id']):
            self.error(*ROLE_PERMISSION_DENIED)
        self.success(item=item)

    @post
    @rule('/delete')
    @form(DeleteForm)
    def delete(self):
        ids = self.form.ids.data
        tag_only = self.form.tag_only.data

        excs = {}

        for id in ids:
            try:
                if self.current_user.role.type == RoleShip.TYPE_ADMIN or tag_only:
                    item = self.docker.image.item(id)
                    if self.current_user.check_permission(OwnerShip.OBJ_TYPE_IMAGE, item['id']):
                        self.docker.image.remove(id, tag_only)

                item = db.query(OwnerShip).filter_by(
                    user_id=self.current_user.id, type=OwnerShip.OBJ_TYPE_IMAGE, obj_id=id).first()
                if item:
                    db.delete_instance(item)
            except APIError as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*DELETE_FAILED, excs=excs)

        self.success(*DELETE_SUCCESS)

    @get
    @rule('/search/<string:keyword>')
    def search(self, keyword):
        self.success(items=self.docker.image.search(keyword))

    @post
    @rule('/pull')
    @form(PullForm)
    def pull(self):
        try:
            item = self.docker.image.pull(**self.form.data)
            db.add_instance(OwnerShip(
                type=OwnerShip.OBJ_TYPE_IMAGE,
                user_id=self.current_user.id,
                obj_id=item['id'],
            ))

            return self.response(*PULL_SUCCESS, item=item)
        except APIError as e:
            self.error(*PULL_FAILED, exc=str(e))

    @post
    @rule('/tag')
    @form(TagForm)
    def tag(self):
        item = self.docker.image.item(self.form.id.data)
        if not item:
            self.error(*OBJECT_NOT_EXISTED)
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_IMAGE, item['id']):
            self.error(*ROLE_PERMISSION_DENIED)

        if self.docker.image.tag(**self.form.data):
            self.success(*TAG_SUCCESS)
        else:
            self.error(*TAG_FAILED)

    @get
    @rule('/history/<string:id>')
    def history(self, id):
        item = self.docker.image.item(id)
        if not item:
            self.error(*OBJECT_NOT_EXISTED)
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_IMAGE, item['id']):
            self.error(*ROLE_PERMISSION_DENIED)

        self.success(histories=self.docker.image.history(id))
