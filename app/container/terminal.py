import fcntl
import json
import os
import pty
import select
import signal
import struct
import subprocess
import termios

from geventwebsocket.websocket import WebSocket
from saika import common, Config, EventSocketController, socket_io
from saika.decorator import controller, rule_rs

from app.libs.docker_sdk import Docker
from app.user import UserService
from .enums import *

GK_FD = 'fd'
GK_CHILD_PID = 'child_pid'
GK_CURRENT_USER = 'currnet_user'
GK_CONTAINER = 'container'
GK_COMMAND = 'command'

EVENT_INIT_SUCCESS = 'init_success'
EVENT_INIT_FAILED = 'init_failed'


@controller('/terminal')
class Terminal(EventSocketController):
    @property
    def docker(self):
        return Docker(Config.section('docker').get('url'))

    @property
    def currnet_user(self):
        return self.context.g_get(GK_CURRENT_USER)

    @property
    def container(self):
        return self.context.g_get(GK_CONTAINER)

    @property
    def command(self):
        return self.context.g_get(GK_COMMAND)

    @rule_rs('/')
    def portal(self, socket: WebSocket):
        self.handle(socket)

    def on_disconnect(self):
        fd = self.context.session.pop(GK_FD, None)
        if fd:
            child_pid = self.context.session.get(GK_CHILD_PID)
            print('Kill: %s %s' % (child_pid, fd))
            try:
                os.kill(child_pid, signal.SIGTERM)
            except ProcessLookupError as e:
                # If process died, skip.
                if not e.errno == 3:
                    raise e
            os.close(fd)

    def on_open(self, user_token, token):
        user = UserService.get_user(user_token)
        if not user:
            self.emit(EVENT_INIT_FAILED, TERMINAL_PERMISSION_DENIED)
            return
        self.context.g_set(GK_CURRENT_USER, user)

        obj = common.obj_decrypt(token)  # type: dict
        if not (obj and obj.get('id') and obj.get('cmd')):
            self.emit(EVENT_INIT_FAILED, TERMINAL_SESSION_INVALID)
            return
        self.context.g_set(GK_COMMAND, obj['cmd'])

        item = self.docker.container.item(obj['id'])
        if not item:
            self.emit(EVENT_INIT_FAILED, TERMINAL_CONTAINER_NOT_EXISTED)
            return
        self.context.g_set(GK_CONTAINER, item)

        (child_pid, fd) = pty.fork()
        if not child_pid:
            subprocess.run(self.command)
        else:
            print('Run: %s %s %s' % (child_pid, fd, ' '.join(self.command)))
            self.context.session[GK_FD] = fd
            self.context.session[GK_CHILD_PID] = child_pid
            self.set_winsize(fd, 20, 30)
            socket_io.start_background_task(target=self.read_and_forward_pty_output, fd=fd, socket=self.socket)
            self.emit(EVENT_INIT_SUCCESS, item)

    def on_pty_input(self, input):
        fd = self.context.session.get(GK_FD)
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
        fd = self.context.session.get(GK_FD)
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
        max_read_bytes = 1024 * 20
        while True:
            try:
                socket_io.sleep(0.018)
                (data_ready, _, _) = select.select([fd], [], [], 0)
                if data_ready:
                    output = os.read(fd, max_read_bytes).decode(errors='ignore')
                    socket.send(json.dumps(dict(event="pty_output", data=dict(output=output))))
            except OSError as e:
                # If process died, end loop.
                if e.errno not in [5, 9]:
                    raise e
                break
