import fcntl
import json
import os
import pty
import select
import signal
import struct
import subprocess
import sys
import termios

from geventwebsocket.websocket import WebSocket
from saika import common, Config, EventSocketController, socket_io, db, Context
from saika.decorator import controller, rule_rs

from app.api.user.models import OwnerShip
from app.libs.docker_sdk import Docker
from .messages import *
from ...api.user.service import UserService
from ...config.docker import DockerConfig

GK_FD = 'fd'
GK_CHILD_PID = 'child_pid'
GK_CURRENT_USER = 'currnet_user'
GK_CONTAINER = 'container'
GK_COMMAND = 'command'

EVENT_INIT_SUCCESS = 'init_success'
EVENT_INIT_FAILED = 'init_failed'


@controller
class Terminal(EventSocketController):
    @rule_rs('/')
    def portal(self, socket: WebSocket):
        self.handle(socket)

    @property
    def docker(self):
        config = Config.get(DockerConfig)  # type: DockerConfig
        return Docker(config.url)

    @property
    def service_user(self):
        return UserService()

    @property
    def currnet_user(self):
        return Context.g_get(GK_CURRENT_USER)

    @property
    def container(self):
        return Context.g_get(GK_CONTAINER)

    @property
    def command(self):
        return Context.g_get(GK_COMMAND)

    def on_disconnect(self):
        fd = Context.session.pop(GK_FD, None)
        if fd:
            child_pid = Context.session.get(GK_CHILD_PID)
            try:
                os.kill(child_pid, signal.SIGTERM)
            except ProcessLookupError as e:
                # If process died, skip.
                if not e.errno == 3:
                    raise e
            os.close(fd)

    def on_open(self, user_token, token):
        user = self.service_user.get_user(user_token)
        if not user:
            self.emit(EVENT_INIT_FAILED, PERMISSION_DENIED)
            return
        Context.g_set(GK_CURRENT_USER, user)

        obj = common.obj_decrypt(token)  # type: dict
        if not (obj and obj.get('id') and obj.get('command')):
            self.emit(EVENT_INIT_FAILED, SESSION_INVALID)
            return
        Context.g_set(GK_COMMAND, obj['command'])

        item = self.docker.container.item(obj['id'])
        if not item:
            self.emit(EVENT_INIT_FAILED, CONTAINER_NOT_EXISTED)
            return
        if not user.check_permission(OwnerShip.OBJ_TYPE_CONTAINER, obj['id']):
            self.emit(EVENT_INIT_FAILED, CONTAINER_PERMISSION_DENIED)
            return
        if item['status'] != 'running':
            self.emit(EVENT_INIT_FAILED, CONTAINER_NOT_RUNNING)
            return

        Context.g_set(GK_CONTAINER, item)

        # Must dispose engine before fork.
        db.dispose_engine()

        (child_pid, fd) = pty.fork()
        if not child_pid:
            # In child process, child_pid = 0
            subprocess.run(self.command)
            sys.exit(0)
        else:
            Context.session[GK_FD] = fd
            Context.session[GK_CHILD_PID] = child_pid
            self.set_winsize(fd, 20, 30)
            socket_io.start_background_task(
                target=self.read_and_forward_pty_output, fd=fd, socket=self.socket
            )
            self.emit(EVENT_INIT_SUCCESS, item)

    def on_pty_input(self, input):
        fd = Context.session.get(GK_FD)
        if not fd:
            return
        try:
            os.write(fd, input.encode())
        except OSError as e:
            # If write input failed, disconnect and kill.
            if e.errno != 5:
                raise e
            self.disconnect()

    def on_resize(self, rows, cols):
        fd = Context.session.get(GK_FD)
        if not fd:
            return

        if fd and rows and cols:
            self.set_winsize(fd, rows, cols)

    @staticmethod
    def set_winsize(fd, row, col, xpix=0, ypix=0):
        winsize = struct.pack("HHHH", row, col, xpix, ypix)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    @staticmethod
    def read_and_forward_pty_output(fd, socket: WebSocket):
        while not socket.closed:
            try:
                socket_io.sleep(0.018)
                (data_ready, _, _) = select.select([fd], [], [], 0)
                if data_ready:
                    output = os.read(fd, 1024 * 20).decode(errors='ignore')
                    socket.send(json.dumps(dict(event="pty_output", data=dict(output=output))))
            except OSError as e:
                # If process died, end loop.
                if e.errno not in [5, 9]:
                    raise e
                break

        socket.close()
