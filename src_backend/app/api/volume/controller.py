from docker.errors import APIError
from saika import db
from saika.decorator import *

from app.api.base import DockerAPIController
from .enums import *
from .forms import *
from ..enums import OBJECT_NOT_EXISTED
from ..user.enums import ROLE_PERMISSION_DENIED
from ..user.models import OwnerShip, RoleShip


@controller
class Volume(DockerAPIController):
    @get
    @rule('/list')
    def list(self):
        items = self.docker.volume.list()
        items = self.current_user.filter_owner(OwnerShip.OBJ_TYPE_VOLUME, items)
        self.success(items=items)

    @get
    @rule('/item/<string:id>')
    def item(self, id):
        item = self.docker.volume.item(id)
        if not item:
            self.error(*OBJECT_NOT_EXISTED)
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_VOLUME, item['id']):
            self.error(*ROLE_PERMISSION_DENIED)
        self.success(item=item)

    @post
    @rule('/delete')
    @form(OperationForm)
    def delete(self):
        ids = self.form.ids.data

        excs = {}

        for id in ids:
            try:
                self.docker.volume.remove(id)

                item = db.query(OwnerShip).filter_by(
                    user_id=self.current_user.id, type=OwnerShip.OBJ_TYPE_VOLUME, obj_id=id).first()
                if item:
                    db.delete_instance(item)
            except APIError as e:
                excs[id] = e

        if len(excs):
            self.error(*DELETE_FAILED, excs=excs)

        self.success(*DELETE_SUCCESS)

    @post
    @rule('/create')
    @form(CreateForm)
    def create(self):
        try:
            data = self.form.data
            if self.current_user.role.type != RoleShip.TYPE_ADMIN:
                data['name'] = '%s_%s' % (self.current_user.username, data['name'])
            item = self.docker.volume.create(**data)
            db.add_instance(OwnerShip(
                type=OwnerShip.OBJ_TYPE_VOLUME,
                user_id=self.current_user.id,
                obj_id=item['id'],
            ))
            return self.response(*CREATE_SUCCESS, item=item)
        except APIError as e:
            self.error(*CREATE_FAILED, exc=e)
