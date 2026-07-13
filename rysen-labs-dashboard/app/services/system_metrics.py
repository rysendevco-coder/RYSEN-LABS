from __future__ import annotations

import logging
import os
import platform
import socket
import time
from dataclasses import asdict, dataclass
from typing import Any

import psutil


logger = logging.getLogger(__name__)


@dataclass
class Usage:
    percent: float | None
    used_gb: float | None = None
    total_gb: float | None = None


@dataclass
class SystemMetrics:
    hostname: str
    uptime_seconds: int | None
    cpu_percent: float | None
    load_average: list[float] | None
    memory: Usage
    disk: Usage
    cpu_temperature_c: float | None
    unavailable: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["uptime_human"] = format_uptime(self.uptime_seconds)
        return payload


def _gb(value: int | float) -> float:
    return round(float(value) / 1024 / 1024 / 1024, 1)


def _cpu_temperature() -> float | None:
    try:
        sensors = psutil.sensors_temperatures(fahrenheit=False)
    except (AttributeError, OSError) as exc:
        logger.info("cpu_temperature_unavailable", exc_info=exc)
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


def collect_system_metrics() -> SystemMetrics:
    unavailable: list[str] = []

    try:
        hostname = socket.gethostname()
    except OSError as exc:
        logger.warning("hostname_unavailable", exc_info=exc)
        hostname = platform.node() or "unknown"
        unavailable.append("hostname")

    try:
        uptime_seconds = int(time.time() - psutil.boot_time())
    except OSError as exc:
        logger.warning("uptime_unavailable", exc_info=exc)
        uptime_seconds = None
        unavailable.append("uptime")

    try:
        cpu_percent = round(psutil.cpu_percent(interval=0.1), 1)
    except OSError as exc:
        logger.warning("cpu_usage_unavailable", exc_info=exc)
        cpu_percent = None
        unavailable.append("cpu")

    try:
        load_average = [round(value, 2) for value in os.getloadavg()]
    except (AttributeError, OSError) as exc:
        logger.info("load_average_unavailable", exc_info=exc)
        load_average = None
        unavailable.append("load_average")

    try:
        memory_stats = psutil.virtual_memory()
        memory = Usage(
            percent=round(float(memory_stats.percent), 1),
            used_gb=_gb(memory_stats.used),
            total_gb=_gb(memory_stats.total),
        )
    except OSError as exc:
        logger.warning("memory_unavailable", exc_info=exc)
        memory = Usage(percent=None)
        unavailable.append("memory")

    try:
        disk_stats = psutil.disk_usage("/")
        disk = Usage(
            percent=round(float(disk_stats.percent), 1),
            used_gb=_gb(disk_stats.used),
            total_gb=_gb(disk_stats.total),
        )
    except OSError as exc:
        logger.warning("disk_unavailable", exc_info=exc)
        disk = Usage(percent=None)
        unavailable.append("disk")

    temperature = _cpu_temperature()
    if temperature is None:
        unavailable.append("cpu_temperature")

    return SystemMetrics(
        hostname=hostname,
        uptime_seconds=uptime_seconds,
        cpu_percent=cpu_percent,
        load_average=load_average,
        memory=memory,
        disk=disk,
        cpu_temperature_c=temperature,
        unavailable=unavailable,
    )
