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
class Network(DockerAPIController):
    @get
    @rule('/list')
    def list(self):
        items = self.docker.network.list()
        items = self.current_user.filter_owner(OwnerShip.OBJ_TYPE_NETWORK, items)
        self.success(items=items)

    @get
    @rule('/item/<string:id>')
    def item(self, id):
        item = self.docker.network.item(id)
        if not item:
            self.error(*OBJECT_NOT_EXISTED)
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_NETWORK, item['id']):
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
                self.docker.network.remove(id)

                item = db.query(OwnerShip).filter_by(
                    user_id=self.current_user.id, type=OwnerShip.OBJ_TYPE_NETWORK, obj_id=id).first()
                if item:
                    db.delete_instance(item)
            except APIError as e:
                excs[id] = str(e)

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
            item = self.docker.network.create(**data)
            db.add_instance(OwnerShip(
                type=OwnerShip.OBJ_TYPE_NETWORK,
                user_id=self.current_user.id,
                obj_id=item['id'],
            ))
            return self.response(*CREATE_SUCCESS, item=item)
        except APIError as e:
            self.error(*CREATE_FAILED, exc=str(e))

    @post
    @rule('/delete')
    @form(OperationForm)
    def delete(self):
        ids = self.form.ids.data

        excs = {}

        for id in ids:
            try:
                self.docker.network.remove(id)

                item = db.query(OwnerShip).filter_by(
                    user_id=self.current_user.id, type=OwnerShip.OBJ_TYPE_NETWORK, obj_id=id).first()
                if item:
                    db.delete_instance(item)
            except APIError as e:
                excs[id] = str(e)
        if len(excs):
            self.error(*DELETE_FAILED, excs=excs)
        self.success(*DELETE_SUCCESS)

    @post
    @rule('/connect')
    @form(ConnectForm)
    def connect(self):
        id = self.form.id.data
        container_id = self.form.container_id.data
        ipv4_address = self.form.ipv4_address.data

        try:
            if self.current_user.check_permission(OwnerShip.OBJ_TYPE_NETWORK, id) and \
                    self.current_user.check_permission(OwnerShip.OBJ_TYPE_CONTAINER, container_id):
                self.docker.network.connect(id, container_id, ipv4_address)
        except APIError as e:
            self.error(*CONNECT_FAILED, exc=str(e))
        self.success(*CONNECT_SUCCESS)

    @post
    @rule('/disconnect')
    @form(DisconnectForm)
    def disconnect(self):
        id = self.form.id.data
        container_id = self.form.container_id.data
        force = self.form.force.data

        try:
            if self.current_user.check_permission(OwnerShip.OBJ_TYPE_NETWORK, id) and \
                    self.current_user.check_permission(OwnerShip.OBJ_TYPE_CONTAINER, container_id):
                self.docker.network.disconnect(id, container_id, force)
        except APIError as e:
            self.error(*DISCONNECT_FAILED, exc=str(e))
        self.success(*DISCONNECT_SUCCESS)
