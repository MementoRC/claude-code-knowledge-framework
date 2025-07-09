"""
UCKN Resource Monitor

- Tracks CPU, memory, I/O usage
- Throttles operations if resources are constrained
- Collects performance metrics
- Health check endpoints
"""

import logging
import threading
import time
from collections.abc import Callable
from typing import Any, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False


class ResourceMonitor:
    """
    Monitors system resources and throttles if needed.
    """

    def __init__(self, interval=2.0, cpu_threshold=90.0, mem_threshold=90.0):
        self.interval = interval
        self.cpu_threshold = cpu_threshold
        self.mem_threshold = mem_threshold
        self.logger = logging.getLogger(__name__)
        self.metrics = []
        self._stop_event = threading.Event()
        self._thread = None
        self._throttle_callback: Callable[[], None] | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _monitor(self):
        while not self._stop_event.is_set():
            usage = self.get_resource_usage()
            self.metrics.append(usage)
            if (
                usage["cpu"] > self.cpu_threshold
                or usage["memory"] > self.mem_threshold
            ):
                self.logger.warning("Resource usage high, throttling triggered.")
                if self._throttle_callback:
                    self._throttle_callback()
            time.sleep(self.interval)

    def get_resource_usage(self) -> dict[str, Any]:
        if PSUTIL_AVAILABLE:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            io = (
                psutil.disk_io_counters()._asdict()
                if hasattr(psutil, "disk_io_counters")
                else {}
            )
        else:
            cpu = 0.0
            mem = 0.0
            io = {}
        return {"cpu": cpu, "memory": mem, "io": io, "timestamp": time.time()}

    def set_throttle_callback(self, callback: Callable[[], None]):
        self._throttle_callback = callback

    def get_metrics(self) -> list:
        return self.metrics

    def health_check(self) -> dict[str, Any]:
        usage = self.get_resource_usage()
        healthy = (
            usage["cpu"] < self.cpu_threshold and usage["memory"] < self.mem_threshold
        )
        return {"healthy": healthy, "usage": usage}


resource_monitor = ResourceMonitor()
