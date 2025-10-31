#!/usr/bin/env python3

#### Import(s) #######################################################################
import json
import time
import socket
import platform
import psutil 

#######################################################################################

#### Internal IP #########################################################################

def get_internal_ip():
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    try:
        s.connect(("1.1.1.1",80 ))
        return s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()


#######################################################################################

#### GET OS INFO #######################################################################

def get_os_info():
    os_name,os_version,os_id = "Linux","",""
    return {
        "kernel_name": platform.system(),
        "kernel_version": platform.release(),
        "os_name": os_name,
        "os_version": os_version,
        "os_id": os_id
    }

#######################################################################################

#### GET DISK USAGE ###################################################################

def get_disk():

    disks = []

    for p in psutil.disk_partitions(all=False):
        if p.fstype in ("tmpfs","devtmpfs","squashfs",""):
            continue
        try:
            u = psutil.disk_usage(p.mountpoint)
            disks.append({
                "mount": p.mountpoint,
                "fs_type": p.fstype,
                "total_gb": round(u.total / (1024**3),2),
                "used_gb": round(u.used / (1024**3),2),
                "pct_used": round(u.percent,2)
            })
        except PermissionError:
            continue
    return disks



### PAYLOAD ##############################################################################

def bulid_payload():

    vm = psutil.virtual_memory()
    return {
        "host": socket.gethostname(),
        "ts": int(time.time()),
        "os": get_os_info(),
        "network": {
            "internal_ip": get_internal_ip()},
        "memory": {
            "memory_total_mb": round(vm.total / (1024**2),2),
            "memory_used_mb": round(vm.used / (1024**2),2),
            "memory_pct_used": round(vm.percent,2)},
        "disk": get_disk(),
    }


#######################################################################################

if __name__ == "__main__":
    print(json.dumps(bulid_payload(), indent=2))