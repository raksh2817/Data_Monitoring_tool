# agent.py
import requests
import socket
import platform
import psutil
from datetime import datetime, timezone
import time
import os


# ======== CONFIG ========

API_URL = "http://127.0.0.1:5000/report"
HOST_KEY = "##host_key_test_1##"
TIMEOUT_SEC = 10
RETRY_COUNT = 2
RETRY_BACKOFF_SEC = 2
# ========================

session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "Authorization": f"Bearer {HOST_KEY}"
})

def get_cpu_pct():
    # shorter sample interval for responsiveness
    return round(psutil.cpu_percent(interval=0.5), 2)

def get_memory():
    mem = psutil.virtual_memory()
    return (
        int(mem.used / 1024 / 1024),
        int(mem.total / 1024 / 1024),
        round(mem.percent, 2),
    )

def get_disk_usage():
    usage = psutil.disk_usage("/")
    return (
        round(usage.used / 1024 / 1024 / 1024, 2),
        round(usage.total / 1024 / 1024 / 1024, 2),
        round(usage.percent, 2),
    )

def get_internal_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1.0)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def collect_metrics():
    mem_used_mb, mem_total_mb, mem_pct = get_memory()
    disk_used_gb, disk_total_gb, disk_pct = get_disk_usage()

    payload = {
        # NOTE: host_key is sent via Authorization header; body field is optional fallback.
        # "host_key": HOST_KEY,

        # Use UTC with timezone info; server strips tz to fit MySQL DATETIME
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),

        "int_ip": get_internal_ip(),
        "public_ip": None,  # optional; fill if you have a method to get it

        # Optional kernel info (kept since API supports these fields)
        "kernel_name": platform.system() or None,
        "kernel_version": platform.release() or None,

        # Metrics
        "cpu_pct": get_cpu_pct(),
        "mem_used_mb": mem_used_mb,
        "mem_total_mb": mem_total_mb,
        "mem_pct": mem_pct,
        "disk_used_gb": disk_used_gb,
        "disk_total_gb": disk_total_gb,
        "disk_pct": disk_pct,

        # Data-pipeline fields (optional)
        "dataset_name": None,
        "partition_key": None,
        "files_count": None,
        "size_bytes": None,
        "min_event_ts": None,
        "max_event_ts": None,

        # Catchall (must be named 'extra' to match server)
        "extra": {
            "agent_version": "0.1.0",
            "hostname": socket.gethostname(),
        }
    }
    return payload

def post_metrics(payload):
    # simple retry loop
    for attempt in range(1, RETRY_COUNT + 2):
        try:
            resp = session.post(API_URL, json=payload, timeout=TIMEOUT_SEC)
            if resp.status_code == 200:
                print(f"[OK] Posted metrics. data_id={resp.json().get('data_id')}")
                return True
            else:
                print(f"[ERR] HTTP {resp.status_code} -> {resp.text}")
        except Exception as e:
            print(f"[EXC] Attempt {attempt}: {e}")

        if attempt <= RETRY_COUNT:
            time.sleep(RETRY_BACKOFF_SEC)
    return False

def main():
    payload = collect_metrics()
    post_metrics(payload)

if __name__ == "__main__":
    main()
