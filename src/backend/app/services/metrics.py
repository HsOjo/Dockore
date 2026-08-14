from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Optional

import psutil
from fastapi import WebSocket

from app.core import config, settings_service
from app.core.database import async_session
from app.schemas.system import DiskGauge, DiskIORates, NetRates, SystemMetrics, UsageGauge

HOST_PROC_ENV = "DOCKORE_HOST_PROC"
METRICS_EVENT = "system.metrics"
ERR_HOST_PROC_NOT_MOUNTED = "host_proc_not_mounted"

_INTERVAL_MIN = 1
_INTERVAL_MAX = 60
_INTERVAL_DEFAULT = 2

# Interfaces that never represent physical host traffic.
_VIRTUAL_NET_PREFIXES = ("lo", "veth", "docker", "br-", "virbr", "vnet", "tun", "tap")


def _container_mode() -> bool:
    """Same convention as StackService: DOCKORE_STACKS_DIR set => container deploy."""
    return bool(config.settings.dockore_stacks_dir)


def _resolve_disk_path() -> str:
    """Partition holding the stacks dir (bind-mounted at the same path in
    container mode, so statvfs on it reflects the host partition)."""
    raw = config.settings.dockore_stacks_dir or str(config.settings.data_dir)
    path = Path(raw)
    while not path.exists() and path != path.parent:
        path = path.parent
    return str(path)


class MetricsSampler:
    """Push host metrics to subscribed /ws connections.

    Sampling runs only while at least one subscriber exists; the interval is
    re-read from settings every round so changes take effect immediately.
    """

    def __init__(self):
        self._subscribers: set[WebSocket] = set()
        self._task: Optional[asyncio.Task] = None
        self._prev_net: Optional[tuple[float, int, int]] = None
        self._prev_disk_io: Optional[tuple[float, int, int]] = None
        self._host_proc_missing = False
        host_proc = os.environ.get(HOST_PROC_ENV, "")
        if _container_mode():
            if host_proc and Path(host_proc).is_dir():
                psutil.PROCFS_PATH = host_proc
            else:
                self._host_proc_missing = True
        self._disk_path = _resolve_disk_path()
        if not self._host_proc_missing:
            psutil.cpu_percent()
            psutil.cpu_times_percent()

    async def subscribe(self, websocket: WebSocket) -> None:
        self._subscribers.add(websocket)
        await websocket.send_json({"type": METRICS_EVENT, "data": self.sample().model_dump()})
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    def unsubscribe(self, websocket: WebSocket) -> None:
        self._subscribers.discard(websocket)
        if not self._subscribers and self._task is not None:
            self._task.cancel()
            self._task = None

    async def _loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(await self._read_interval())
                payload = {"type": METRICS_EVENT, "data": self.sample().model_dump()}
                dead = []
                for ws in self._subscribers:
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    self.unsubscribe(ws)
        except asyncio.CancelledError:
            pass

    async def _read_interval(self) -> float:
        try:
            async with async_session() as session:
                all_settings = await settings_service.get_all(session)
            value = float(all_settings.get("metrics_interval", _INTERVAL_DEFAULT))
            return min(max(value, _INTERVAL_MIN), _INTERVAL_MAX)
        except Exception:
            return float(_INTERVAL_DEFAULT)

    def sample(self) -> SystemMetrics:
        if self._host_proc_missing:
            return SystemMetrics(error=ERR_HOST_PROC_NOT_MOUNTED)

        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage(self._disk_path)
        io_delay = getattr(psutil.cpu_times_percent(), "iowait", None)
        net_in, net_out = self._net_rates()
        disk_read, disk_write = self._disk_io_rates()
        load: Optional[list[float]] = None
        if hasattr(os, "getloadavg"):
            load = [round(v, 2) for v in os.getloadavg()]

        return SystemMetrics(
            timestamp=time.time(),
            cpu_percent=psutil.cpu_percent(),
            cpu_count=psutil.cpu_count() or 0,
            io_delay=io_delay,
            memory=UsageGauge(total=mem.total, used=mem.used, percent=mem.percent),
            swap=UsageGauge(total=swap.total, used=swap.used, percent=swap.percent),
            disk=DiskGauge(
                path=self._disk_path,
                total=disk.total,
                used=disk.used,
                percent=round(disk.used / disk.total * 100, 1) if disk.total else 0.0,
            ),
            load_avg=load,
            net=NetRates(in_rate=net_in, out_rate=net_out),
            disk_io=DiskIORates(read_rate=disk_read, write_rate=disk_write),
            uptime=max(0.0, time.time() - psutil.boot_time()),
        )

    def _net_rates(self) -> tuple[Optional[float], Optional[float]]:
        now = time.monotonic()
        recv = sent = 0
        for name, nic in psutil.net_io_counters(pernic=True).items():
            if name.startswith(_VIRTUAL_NET_PREFIXES):
                continue
            recv += nic.bytes_recv
            sent += nic.bytes_sent
        prev = self._prev_net
        self._prev_net = (now, recv, sent)
        if prev is None:
            return None, None
        elapsed = now - prev[0]
        if elapsed <= 0:
            return None, None
        return (recv - prev[1]) / elapsed, (sent - prev[2]) / elapsed

    def _disk_io_rates(self) -> tuple[Optional[float], Optional[float]]:
        counters = psutil.disk_io_counters()
        if counters is None:
            return None, None
        now = time.monotonic()
        prev = self._prev_disk_io
        self._prev_disk_io = (now, counters.read_bytes, counters.write_bytes)
        if prev is None:
            return None, None
        elapsed = now - prev[0]
        if elapsed <= 0:
            return None, None
        return (
            (counters.read_bytes - prev[1]) / elapsed,
            (counters.write_bytes - prev[2]) / elapsed,
        )


sampler = MetricsSampler()
