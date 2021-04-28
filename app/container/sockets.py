import fcntl
import os
import pty
import select
import signal
import struct
import subprocess
import termios

from saika import socket_io, SocketIOController, common, Config
from saika.decorator import on_namespace

from app.libs.docker_sdk import Docker
from app.user import UserService
from .enums import *

GK_FD = 'fd'
GK_CHILD_PID = 'child_pid'


@on_namespace('/terminal')
class Terminal(SocketIOController):
    @property
    def docker(self):
        return Docker(Config.section('docker').get('url'))

    def on_connect(self):
        print('Connect: %s' % self.sid)

    def on_disconnect(self):
        print('Disconnect: %s' % self.sid)
        fd = self.context.session.pop(GK_FD, None)
        if fd:
            child_pid = self.context.session.get(GK_CHILD_PID)
            print('Kill: %s %s' % (child_pid, fd))
            os.kill(child_pid, signal.SIGTERM)
            os.close(fd)

    def on_open(self, *args):
        if len(args) != 2:
            return
        [user_token, obj_str] = args
        user = UserService.get_user(user_token)
        if not user:
            self.emit('init_failed', TERMINAL_PERMISSION_DENIED)
            return

        obj = common.obj_decrypt(obj_str)  # type: dict
        if not (obj and obj.get('id') and obj.get('cmd')):
            self.emit('init_failed', TERMINAL_SESSION_INVALID)
            return

        item = self.docker.container.item(obj['id'])
        if not item:
            self.emit('init_failed', TERMINAL_CONTAINER_NOT_EXISTED)
            return

        cmd = obj['cmd']

        (child_pid, fd) = pty.fork()
        if not child_pid:
            subprocess.run(cmd)
        else:
            print('Run: %s %s %s' % (child_pid, fd, ' '.join(cmd)))
            self.context.session[GK_FD] = fd
            self.context.session[GK_CHILD_PID] = child_pid
            self.set_winsize(fd, 20, 30)
            socket_io.start_background_task(target=self.read_and_forward_pty_output, fd=fd, sid=self.sid)
            self.emit('init_success', item)

    def on_pty_input(self, *args):
        if len(args) != 1:
            return
        [data] = args
        if not isinstance(data, dict):
            return
        fd = self.context.session.get(GK_FD)
        if not fd:
            return
        try:
            os.write(fd, data["input"].encode())
        except OSError as e:
            if e.errno == 5:
                self.disconnect()

    def on_resize(self, *args):
        if len(args) != 1:
            return
        [data] = args
        if not isinstance(data, dict):
            return
        fd = self.context.session.get(GK_FD)
        if not fd:
            return

        rows = int(data.get('rows'))
        cols = int(data.get('cols'))

        if rows and cols:
            self.set_winsize(fd, rows, cols)

    @staticmethod
    def set_winsize(fd, row, col, xpix=0, ypix=0):
        winsize = struct.pack("HHHH", row, col, xpix, ypix)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)

    def read_and_forward_pty_output(self, fd, sid):
        max_read_bytes = 1024 * 20
        while True:
            try:
                socket_io.sleep(0.01)
                timeout_sec = 0
                (data_ready, _, _) = select.select([fd], [], [], timeout_sec)
                if data_ready:
                    output = os.read(fd, max_read_bytes).decode(errors='ignore')
                    self.emit("pty_output", {"output": output}, room=sid)
            except OSError as e:
                if e.errno == 9:
                    break
                else:
                    raise e

        self.disconnect(sid=sid)
