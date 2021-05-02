from docker.errors import APIError
from saika.decorator import *

from app.base import DockerAPIController
from .enums import *
from .forms import *
from .terminal import *
from ..user.enums import ROLE_PERMISSION_DENIED
from ..user.models import OwnerShip, RoleShip


@controller('/api/container')
class Container(DockerAPIController):
    @get
    @rule('/list')
    @form(ListForm)
    def list(self):
        items = self.docker.container.list(all=self.form.is_all.data)
        items = self.current_user.filter_owner(OwnerShip.OBJ_TYPE_CONTAINER, items)
        self.success(items=items)

    @get
    @rule('/item/<string:id>')
    def item(self, id: str):
        item = self.docker.container.item(id)
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_CONTAINER, item['id']):
            self.error(*ROLE_PERMISSION_DENIED)
        self.success(item=item)

    @post
    @rule('/delete')
    @form(OperationForm)
    def delete(self):
        ids = self.form.ids.data
        ids = self.current_user.filter_owner_ids(OwnerShip.OBJ_TYPE_CONTAINER, ids)

        excs = {}

        for id in ids:
            try:
                self.docker.container.remove(id)

                item = db.query(OwnerShip).filter_by(
                    user_id=self.current_user.id, type=OwnerShip.OBJ_TYPE_CONTAINER, obj_id=id).first()
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
            if self.current_user.role != RoleShip.TYPE_ADMIN:
                data['name'] = '%s_%s' % (self.current_user.username, data['name'])
            item = self.docker.container.create(**data)
            db.add_instance(OwnerShip(
                type=OwnerShip.OBJ_TYPE_CONTAINER,
                user_id=self.current_user.id,
                obj_id=item['id'],
            ))
            return self.response(*CREATE_SUCCESS, item=item)
        except APIError as e:
            self.error(*CREATE_FAILED, exc=str(e))

    @post
    @rule('/run')
    @form(CreateForm)
    def run(self):
        try:
            data = self.form.data
            if self.current_user.role != RoleShip.TYPE_ADMIN:
                data['name'] = '%s_%s' % (self.current_user.username, data['name'])
            item = self.docker.container.run(**data)
            db.add_instance(OwnerShip(
                type=OwnerShip.OBJ_TYPE_CONTAINER,
                user_id=self.current_user.id,
                obj_id=item['id'],
            ))
            return self.response(*RUN_SUCCESS, item=item)
        except APIError as e:
            self.error(*RUN_FAILED, exc=str(e))

    @post
    @rule('/start')
    @form(OperationForm)
    def start(self):
        ids = self.form.ids.data
        ids = self.current_user.filter_owner_ids(OwnerShip.OBJ_TYPE_CONTAINER, ids)

        excs = {}
        for id in ids:
            try:
                self.docker.container.start(id)
            except APIError as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*START_FAILED, excs=excs)

        self.success(*START_SUCCESS)

    @post
    @rule('/stop')
    @form(StopForm)
    def stop(self):
        ids = self.form.ids.data
        ids = self.current_user.filter_owner_ids(OwnerShip.OBJ_TYPE_CONTAINER, ids)
        timeout = int(self.form.timeout.data / len(ids))

        excs = {}
        for id in ids:
            try:
                self.docker.container.stop(id, timeout)
            except APIError as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*STOP_FAILED, excs=excs)

        self.success(*STOP_SUCCESS)

    @post
    @rule('/restart')
    @form(StopForm)
    def restart(self):
        ids = self.form.ids.data
        ids = self.current_user.filter_owner_ids(OwnerShip.OBJ_TYPE_CONTAINER, ids)
        timeout = int(self.form.timeout.data / len(ids))

        excs = {}
        for id in ids:
            try:
                self.docker.container.restart(id, timeout)
            except APIError as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*RESTART_FAILED, excs=excs)

        self.success(*RESTART_SUCCESS)

    @post
    @rule('/rename')
    @form(RenameForm)
    def rename(self):
        try:
            if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_CONTAINER, self.form.id.data):
                self.error(*ROLE_PERMISSION_DENIED)

            self.docker.container.rename(**self.form.data)
            return self.response(*RENAME_SUCCESS)
        except APIError as e:
            self.error(*RENAME_FAILED, exc=str(e))

    @post
    @rule('/logs')
    @form(LogsForm)
    def logs(self):
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_CONTAINER, self.form.id.data):
            self.error(*ROLE_PERMISSION_DENIED)

        self.success(content=self.docker.container.logs(
            **self.form.data
        ))

    @get
    @rule('/diff/<string:id>')
    def diff(self, id):
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_CONTAINER, id):
            self.error(*ROLE_PERMISSION_DENIED)

        self.success(files=self.docker.container.diff(id))

    @post
    @rule('/commit')
    @form(CommitForm)
    def commit(self):
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_CONTAINER, self.form.id.data):
            self.error(*ROLE_PERMISSION_DENIED)

        self.success(*COMMIT_SUCCESS, content=self.docker.container.commit(
            **self.form.data
        ))

    @post
    @rule('/terminal')
    @form(TerminalForm)
    def terminal(self):
        if not self.current_user.check_permission(OwnerShip.OBJ_TYPE_CONTAINER, self.form.id.data):
            self.error(*ROLE_PERMISSION_DENIED)

        item = self.docker.container.item(self.form.id.data)
        if not item:
            self.error(*TERMINAL_FAILED_NOT_EXISTED)

        cfg = Config.section('docker')

        expires = cfg.get('terminal_expires', 600)
        cmd = [cfg.get('cli_bin'), '-H', cfg.get('url')]

        if self.form.cmd.data:
            cmd += ['exec', '-it', item['id'], *self.form.cmd.data.split(' ')]
        else:
            cmd += ['attach', item['id']]

        if item['tty'] and item['interactive']:
            self.success(token=common.obj_encrypt(dict(id=item['id'], cmd=cmd), expires))
        else:
            self.error(*TERMINAL_FAILED)
