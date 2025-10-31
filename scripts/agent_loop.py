#!/usr/bin/env python3

#### Import(s) #######################################################################
import os
import time
import json
import socket
import platform
import psutil
import requests
import subprocess


INTERVAL = int(os.getenv("INTERVAL","60")) # every 60 seconds it gets refresehed 
SERVER_URL = os.getenv("SERVER_URL","http://127.0.0.1:5000/api/v1/metrics") # flask server url
HOST_TOKEN = os.getenv("HOST_TOKEN","HOST_TOKEN_123") # token to authenticate with the server


## FUNCTION(s) ###########################################################################

## Get internal IP address
def internal_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("1.1.1.1", 80))
        return s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()

## Get disk usage
def get_disks():
    disks = []
    for p in psutil.disk_partitions(all=False):
        if p.fstype in ("tmpfs", "devtmpfs", "squashfs", ""):
            continue
        try:
            u = psutil.disk_usage(p.mountpoint)
            disks.append({
                "mount": p.mountpoint,
                "fs_type": p.fstype,
                "total_gb": round(u.total/1024**3, 2),
                "used_gb": round(u.used/1024**3, 2),
                "pct_used": round(u.percent, 2),
            })
        except PermissionError:
            continue
    return disks

## Prepare payload once
def payload_once():
    vm = psutil.virtual_memory()
    return {
        "host": socket.gethostname(),
        "ts": int(time.time()),
        "os": {
            "kernel_name": platform.system(),
            "kernel_version": platform.release(),
            "architecture": platform.machine(),
        },
        "network": {"internal_ip": internal_ip()},
        "memory": {
            "mem_total_mb": vm.total // (1024**2),
            "mem_used_mb": vm.used // (1024**2),
            "mem_pct": vm.percent
        },
        "disks": get_disks()
    }

## Post with retries
def post_with_retries(url, headers, json_body, attempts=3):
    backoff = 1
    for i in range(1, attempts+1):
        try:
            r = requests.post(url, headers=headers, json=json_body, timeout=5)
            return r
        except requests.exceptions.RequestException as e:
            print(time.strftime("[%H:%M:%S]"), f"WARN attempt {i}/{attempts}:", e)
            if i == attempts:
                return None
            time.sleep(backoff)
            backoff *= 2  # 1s -> 2s -> 4s


## Main loop
def main():
    while True:
        data = payload_once()
        r = post_with_retries(
            SERVER_URL,
            headers={"Authorization": f"Bearer {HOST_TOKEN}"},
            json_body=data,
            attempts=3
        )
        if r is None:
            print(time.strftime("[%H:%M:%S]"), "ERROR giving up after retries")
        else:
            print(time.strftime("[%H:%M:%S]"), "POST", r.status_code, r.text[:200])
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()