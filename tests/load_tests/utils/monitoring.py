"""
Resource and performance monitoring for UCKN load tests.
"""

import os
import threading
import time

import psutil

_MONITOR_THREAD = None
_MONITOR_STOP = False


def monitor_resources(interval=1.0, log_file="resource_usage.log"):
    global _MONITOR_STOP
    with open(log_file, "w") as f:
        f.write(
            "timestamp,cpu_percent,mem_percent,mem_used_mb,disk_read_mb,disk_write_mb\n"
        )
        while not _MONITOR_STOP:
            ts = time.time()
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            mem_used = mem.used / (1024 * 1024)
            disk = psutil.disk_io_counters()
            disk_read = disk.read_bytes / (1024 * 1024)
            disk_write = disk.write_bytes / (1024 * 1024)
            f.write(
                f"{ts},{cpu},{mem.percent},{mem_used:.2f},{disk_read:.2f},{disk_write:.2f}\n"
            )
            f.flush()
            time.sleep(interval)


def start_resource_monitor(interval=1.0, log_file="resource_usage.log"):
    global _MONITOR_THREAD, _MONITOR_STOP
    if _MONITOR_THREAD is not None:
        return
    _MONITOR_STOP = False
    _MONITOR_THREAD = threading.Thread(
        target=monitor_resources, args=(interval, log_file), daemon=True
    )
    _MONITOR_THREAD.start()


def stop_resource_monitor():
    global _MONITOR_THREAD, _MONITOR_STOP
    _MONITOR_STOP = True
    if _MONITOR_THREAD is not None:
        _MONITOR_THREAD.join(timeout=2)
        _MONITOR_THREAD = None
