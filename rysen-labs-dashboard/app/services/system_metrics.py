from __future__ import annotations

import logging
import os
import platform
import socket
import time

import psutil

from app.models.schemas import SystemMetrics, Usage


logger = logging.getLogger(__name__)


def _gb(value: int | float) -> float:
    return round(float(value) / 1024 / 1024 / 1024, 1)


def format_uptime(seconds: int | None) -> str:
    if seconds is None:
        return "Unavailable"
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _cpu_temperature() -> float | None:
    try:
        sensors = psutil.sensors_temperatures(fahrenheit=False)
    except (AttributeError, OSError):
        logger.info("cpu_temperature_unavailable", extra={"event": "cpu_temperature_unavailable"})
        return None

    preferred_labels = ("coretemp", "k10temp", "cpu_thermal", "acpitz")
    for label in preferred_labels:
        readings = sensors.get(label) or []
        values = [reading.current for reading in readings if reading.current is not None]
        if values:
            return round(max(values), 1)

    for readings in sensors.values():
        values = [reading.current for reading in readings if reading.current is not None]
        if values:
            return round(max(values), 1)
    return None


def collect_system_metrics() -> SystemMetrics:
    unavailable: list[str] = []

    try:
        hostname = socket.gethostname()
    except OSError:
        logger.warning("hostname_unavailable", extra={"event": "hostname_unavailable"})
        hostname = platform.node() or "unknown"
        unavailable.append("hostname")

    try:
        uptime_seconds = int(time.time() - psutil.boot_time())
    except OSError:
        logger.warning("uptime_unavailable", extra={"event": "uptime_unavailable"})
        uptime_seconds = None
        unavailable.append("uptime")

    try:
        cpu_percent = round(psutil.cpu_percent(interval=0.1), 1)
    except OSError:
        logger.warning("cpu_usage_unavailable", extra={"event": "cpu_usage_unavailable"})
        cpu_percent = None
        unavailable.append("cpu")

    try:
        load_average = [round(value, 2) for value in os.getloadavg()]
    except (AttributeError, OSError):
        load_average = None
        unavailable.append("load_average")

    try:
        memory_stats = psutil.virtual_memory()
        memory = Usage(
            percent=round(float(memory_stats.percent), 1),
            used_gb=_gb(memory_stats.used),
            total_gb=_gb(memory_stats.total),
        )
    except OSError:
        logger.warning("memory_unavailable", extra={"event": "memory_unavailable"})
        memory = Usage(percent=None)
        unavailable.append("memory")

    try:
        disk_stats = psutil.disk_usage("/")
        disk = Usage(
            percent=round(float(disk_stats.percent), 1),
            used_gb=_gb(disk_stats.used),
            total_gb=_gb(disk_stats.total),
        )
    except OSError:
        logger.warning("disk_unavailable", extra={"event": "disk_unavailable"})
        disk = Usage(percent=None)
        unavailable.append("disk")

    temperature = _cpu_temperature()
    if temperature is None:
        unavailable.append("cpu_temperature")

    return SystemMetrics(
        hostname=hostname,
        uptime_seconds=uptime_seconds,
        uptime_human=format_uptime(uptime_seconds),
        cpu_percent=cpu_percent,
        load_average=load_average,
        memory=memory,
        disk=disk,
        cpu_temperature_c=temperature,
        unavailable=unavailable,
    )
