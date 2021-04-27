from docker.errors import APIError
from saika.decorator import *

from app.base import DockerAPIController
from .enums import *
from .forms import *
from .sockets import *


@controller('/api/container')
class Container(DockerAPIController):
    @get
    @rule('/list')
    @form(ListForm)
    def list(self):
        self.success(
            items=self.docker.container.list(all=self.form.is_all.data)
        )

    @get
    @rule('/item/<string:id>')
    def item(self, id: str):
        self.success(
            item=self.docker.container.item(id)
        )

    @post
    @rule('/delete')
    @form(OperationForm)
    def delete(self):
        ids = self.form.ids.data

        excs = {}

        for id in ids:
            try:
                self.docker.container.remove(id)
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
            return self.response(*CREATE_SUCCESS, item=self.docker.container.create(**self.form.data))
        except APIError as e:
            self.error(*CREATE_FAILED, exc=str(e))

    @post
    @rule('/run')
    @form(CreateForm)
    def run(self):
        try:
            return self.response(*RUN_SUCCESS, item=self.docker.container.run(**self.form.data))
        except APIError as e:
            self.error(*RUN_FAILED, exc=str(e))

    @post
    @rule('/start')
    @form(OperationForm)
    def start(self):
        ids = self.form.ids.data

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
            return self.response(*RENAME_SUCCESS, item=self.docker.container.rename(
                **self.form.data
            ))
        except APIError as e:
            self.error(*RENAME_FAILED, exc=str(e))

    @post
    @rule('/logs')
    @form(LogsForm)
    def logs(self):
        self.success(content=self.docker.container.logs(
            **self.form.data
        ))

    @get
    @rule('/diff/<string:id>')
    def diff(self, id):
        self.success(files=self.docker.container.diff(id))

    @post
    @rule('/commit')
    @form(CommitForm)
    def commit(self):
        self.success(*COMMIT_SUCCESS, content=self.docker.container.commit(
            **self.form.data
        ))

    @post
    @rule('/terminal')
    @form(TerminalForm)
    def terminal(self):
        item = self.docker.container.item(self.form.id.data)
        if not item:
            self.error(*TERMINAL_FAILED_NOT_EXISTED)

        cfg = Config.section('docker')

        expires = cfg.get('shell_expires', 600)
        cmd = [cfg.get('cli-bin'), '-H', cfg.get('url')]

        if self.form.cmd.data:
            cmd += ['exec', '-it', item['id'], *self.form.cmd.data.split(' ')]
        else:
            cmd += ['attach', item['id']]

        if item['tty'] and item['interactive']:
            self.success(token=common.obj_encrypt(dict(id=item['id'], cmd=cmd), expires))
        else:
            self.error(*TERMINAL_FAILED)
