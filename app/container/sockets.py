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

GK_FD = 'fd'
GK_CHILD_PID = 'child_pid'


@on_namespace('/terminal')
class Terminal(SocketIOController):
    @property
    def docker(self):
        return Docker(Config.section('docker').get('url'))

    def on_disconnect(self):
        fd = self.context.session.pop(GK_FD, None)
        if fd:
            child_pid = self.context.session.get(GK_CHILD_PID)
            print('Kill: %d %d' % (child_pid, fd))
            os.kill(child_pid, signal.SIGTERM)
            os.close(fd)

    def on_open(self, obj_str):
        obj = common.obj_decrypt(obj_str)  # type: dict
        if not (obj and obj.get('id')):
            self.emit('auth_failed')
            return

        item = self.docker.container.item(obj['id'])
        if not item:
            self.emit('auth_failed')
            return

        self.emit('auth_success', item)
        cfg = Config.section('docker')
        cmd = [cfg.get('cli-bin'), '-H', cfg.get('url'), 'attach', item['id']]

        (child_pid, fd) = pty.fork()
        if child_pid == 0:
            subprocess.run(cmd)
        else:
            print('Run: %d %d %s' % (child_pid, fd, ' '.join(cmd)))
            self.context.session[GK_FD] = fd
            self.context.session[GK_CHILD_PID] = child_pid
            self.set_winsize(fd, 20, 30)
            socket_io.start_background_task(target=self.read_and_forward_pty_output, fd=fd, sid=self.sid)

    def on_pty_input(self, data):
        if not isinstance(data, dict):
            return
        fd = self.context.session.get(GK_FD)
        if not fd:
            return
        os.write(fd, data["input"].encode())

    def on_resize(self, data):
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
