#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitoring Agent - Collects system metrics and sends to API server
Runs on client machines to report data to the central monitoring system
"""

import os
import socket
import platform
import psutil
import json
import sys
from datetime import datetime
import requests
from pathlib import Path

# ---- CONFIGURATION ----
# Load from config file or environment variables
CONFIG_FILE = Path(__file__).parent / "agent_config.json"

def load_config():
    """Load configuration from file or create default"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        # Default configuration
        default_config = {
            "api_url": "http://192.168.1.35:5000/report",
            "host_key": "test-key-123",  # CHANGE THIS for each host
            "report_interval_seconds": 60
        }
        # Save default config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Created default config at {CONFIG_FILE}")
        print("Please edit this file with your API URL and host key")
        return default_config

CONFIG = load_config()
API_URL = CONFIG.get("api_url", "http://192.168.1.35:5000/report")
HOST_KEY = CONFIG.get("host_key", "test-key-123")

# ---- METRIC COLLECTORS ----

def get_cpu():
    """Get CPU usage percentage"""
    try:
        return round(psutil.cpu_percent(interval=1), 2)
    except Exception as e:
        print(f"Error getting CPU: {e}")
        return None

def get_memory():
    """Get memory usage (used MB, total MB, percentage)"""
    try:
        mem = psutil.virtual_memory()
        return {
            "used_mb": int(mem.used // (1024**2)),
            "total_mb": int(mem.total // (1024**2)),
            "percent": round(mem.percent, 2)
        }
    except Exception as e:
        print(f"Error getting memory: {e}")
        return {"used_mb": None, "total_mb": None, "percent": None}

def get_disk_usage():
    """Get disk usage (used GB, total GB, percentage)"""
    try:
        usage = psutil.disk_usage('/')
        return {
            "used_gb": round(usage.used / (1024 ** 3), 2),
            "total_gb": round(usage.total / (1024 ** 3), 2),
            "percent": round(usage.percent, 2)
        }
    except Exception as e:
        print(f"Error getting disk usage: {e}")
        return {"used_gb": None, "total_gb": None, "percent": None}

def get_hostname():
    """Get system hostname"""
    try:
        return socket.gethostname()
    except Exception as e:
        print(f"Error getting hostname: {e}")
        return "unknown"

def get_os():
    """Get OS name and version"""
    try:
        return platform.system(), platform.release()
    except Exception as e:
        print(f"Error getting OS: {e}")
        return "Unknown", "Unknown"

def get_kernel():
    """Get kernel name and version"""
    try:
        return platform.system(), platform.version()
    except Exception as e:
        print(f"Error getting kernel: {e}")
        return "Unknown", "Unknown"

def get_internal_ip():
    """Get internal IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Error getting internal IP: {e}")
        return None

# ---- MAIN REPORTING FUNCTION ----

def collect_and_send_metrics():
    """Collect all metrics and send to API"""
    
    # Collect all metrics
    kernel_name, kernel_version = get_kernel()
    mem = get_memory()
    disk = get_disk_usage()
    
    payload = {
        "host_key": HOST_KEY,
        "collected_at": datetime.now().isoformat(),
        "int_ip": get_internal_ip(),
        "kernel_name": kernel_name,
        "kernel_version": kernel_version,
        "cpu_pct": get_cpu(),
        "mem_used_mb": mem["used_mb"],
        "mem_total_mb": mem["total_mb"],
        "mem_pct": mem["percent"],
        "disk_used_gb": disk["used_gb"],
        "disk_total_gb": disk["total_gb"],
        "disk_pct": disk["percent"]
    }
    
    # Print what we're sending (for debugging)
    print(f"\n{'='*60}")
    print(f"Timestamp: {payload['collected_at']}")
    print(f"Hostname: {get_hostname()}")
    print(f"Internal IP: {payload['int_ip']}")
    print(f"CPU: {payload['cpu_pct']}%")
    print(f"Memory: {payload['mem_used_mb']}/{payload['mem_total_mb']} MB ({payload['mem_pct']}%)")
    print(f"Disk: {payload['disk_used_gb']}/{payload['disk_total_gb']} GB ({payload['disk_pct']}%)")
    print(f"{'='*60}")
    
    # Send to API
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {HOST_KEY}"
        }
        
        print(f"\nSending to: {API_URL}")
        response = requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Success! Data ID: {result.get('data_id')}")
            return True
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection Error: Cannot reach {API_URL}")
        print(f"  Make sure the Flask server is running and accessible")
        print(f"  Error: {e}")
        return False
    except requests.exceptions.Timeout:
        print(f"✗ Timeout: Server took too long to respond")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def main():
    """Main entry point"""
    print(f"\n{'='*60}")
    print(f"Monitoring Agent Starting")
    print(f"{'='*60}")
    print(f"API URL: {API_URL}")
    print(f"Host Key: {HOST_KEY[:8]}... (masked)")
    print(f"Config File: {CONFIG_FILE}")
    
    # Check if using default key
    if HOST_KEY == "test-key-123":
        print("\n⚠ WARNING: Using default test key!")
        print("  For production, change the host_key in agent_config.json")
    
    print(f"\n{'='*60}\n")
    
    # Run once and exit (for testing)
    # For production, you'd run this in a loop or via cron
    success = collect_and_send_metrics()
    
    if success:
        print("\n✓ Agent run completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Agent run failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
