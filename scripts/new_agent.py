#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
import platform
import psutil
from datetime import datetime
import mysql.connector

# ---- DATABASE CONFIGURATION ----
DB_HOST = 'mysql.clarksonmsda.org'
DB_USER = 'srinatr'
DB_PASSWORD = '7CLs7jxjQu5VG3T'
DB_NAME = 'srinatr_monitor'


# ---- METRIC COLLECTORS ----

def get_cpu():
    return round(psutil.cpu_percent(interval=1), 2)

def get_memory():
    mem = psutil.virtual_memory()
    return int(mem.used // (1024**2)), int(mem.total // (1024**2)), round(mem.percent, 2)  # used, total (MB), pct

def get_disk_usage():
    usage = psutil.disk_usage('/')
    return round(usage.used / (1024 ** 3), 2), round(usage.total / (1024 ** 3), 2), round(usage.percent, 2)  # used, total (GB), pct

def get_hostname():
    return socket.gethostname()

def get_os():
    return platform.system(), platform.release()

def get_kernel():
    return platform.system(), platform.version()

def get_internal_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

# ---- HOST UPSERT FUNCTION ----

def get_or_create_host_id(conn, host_name, os_name, os_version):
    cursor = conn.cursor()
    cursor.execute("SELECT host_id FROM hosts WHERE host_name = %s", (host_name,))
    result = cursor.fetchone()
    if result:
        host_id = result[0]
        cursor.execute(
            "UPDATE hosts SET os_name=%s, os_version=%s, is_active=1, last_seen=%s WHERE host_id=%s",
            (os_name, os_version, datetime.now(), host_id)
        )
        conn.commit()
    else:
        cursor.execute(
            "INSERT INTO hosts (host_name, os_name, os_version, is_active, last_seen, created_at) VALUES (%s, %s, %s, 1, %s, %s)",
            (host_name, os_name, os_version, datetime.now(), datetime.now())
        )
        conn.commit()
        host_id = cursor.lastrowid
    cursor.close()
    return host_id

# ---- METRIC INSERT FUNCTION ----

def insert_metrics(conn, host_id, int_ip, kernel_name, kernel_version, cpu, mem_used, mem_total, mem_pct, disk_used, disk_total, disk_pct):
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("""
        INSERT INTO incoming_data (
            host_id, collected_at, created_at,
            int_ip, kernel_name, kernel_version,
            cpu_pct, mem_used_mb, mem_total_mb, mem_pct,
            disk_used_gb, disk_total_gb, disk_pct
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s
        )
        """, (
            host_id, now, now,
            int_ip, kernel_name, kernel_version,
            cpu, mem_used, mem_total, mem_pct,
            disk_used, disk_total, disk_pct
        )
    )
    conn.commit()
    cursor.close()

# ---- MAIN ----

def main():
    host_name = get_hostname()
    os_name, os_version = get_os()
    kernel_name, kernel_version = get_kernel()
    int_ip = get_internal_ip()
    cpu = get_cpu()
    mem_used, mem_total, mem_pct = get_memory()
    disk_used, disk_total, disk_pct = get_disk_usage()

    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    try:
        host_id = get_or_create_host_id(conn, host_name, os_name, os_version)
        insert_metrics(conn, host_id, int_ip, kernel_name, kernel_version, cpu, mem_used, mem_total, mem_pct, disk_used, disk_total, disk_pct)
        print(f"Inserted metrics for host '{host_name}' (ID {host_id}) at {datetime.now().isoformat()}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
