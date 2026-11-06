import platform
import socket
import time

import psutil

def collect_system_metrics() -> dict:
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\" if platform.system() == "Windows" else "/")
    network = psutil.net_io_counters()

    return {
        "cpu_percent": cpu,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "network_sent_bytes": network.bytes_sent,
        "network_received_bytes": network.bytes_recv,
        "details": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "boot_time": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime(psutil.boot_time()),
            ),
            "logical_cpu_count": psutil.cpu_count(),
            "physical_cpu_count": psutil.cpu_count(logical=True),
            "total_memory_bytes": memory.total,
            "available_memory_bytes": memory.available,
        },
    }

def collect_process_summary() -> list[dict]:
    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "username", "status"]
    ):
        try:
            processes.append(process.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return processes[:100]
