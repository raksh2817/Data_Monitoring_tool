#!/usr/bin/env python3
"""
Test Script - Simulates Multiple Hosts Reporting Data
Run this to populate the database with realistic monitoring data
"""

import requests
import random
import time
from datetime import datetime
import json
from flask import Flask, render_template

app = Flask(__name__)

# Configuration
API_URL = "http://localhost:5000/report"
SCENARIOS = {
    "normal": {
        "host_key": "test-key-123",
        "host_name": "web-server-01",
        "cpu": (5, 40),      # Range: 5-40%
        "memory": (30, 60),  # Range: 30-60%
        "disk": (20, 50),    # Range: 20-50%
    },
    "high_cpu": {
        "host_key": "high-cpu-server",
        "host_name": "api-server-02",
        "cpu": (85, 95),     # High CPU usage
        "memory": (30, 50),
        "disk": (20, 40),
    },
    "high_memory": {
        "host_key": "high-mem-server",
        "host_name": "db-server-03",
        "cpu": (10, 30),
        "memory": (93, 99),  # High memory usage
        "disk": (30, 50),
    },
    "high_disk": {
        "host_key": "high-disk-server",
        "host_name": "storage-server-04",
        "cpu": (5, 20),
        "memory": (20, 40),
        "disk": (95, 99),    # High disk usage
    },
}

def generate_metrics(scenario):
    """Generate realistic metrics based on scenario"""
    ranges = SCENARIOS[scenario]
    
    # Generate random values within ranges
    cpu = round(random.uniform(ranges["cpu"][0], ranges["cpu"][1]), 2)
    mem_pct = round(random.uniform(ranges["memory"][0], ranges["memory"][1]), 2)
    disk_pct = round(random.uniform(ranges["disk"][0], ranges["disk"][1]), 2)
    
    # Calculate actual values
    mem_total = 16384  # 16GB
    mem_used = int(mem_total * mem_pct / 100)
    
    disk_total = 500.0  # 500GB
    disk_used = round(disk_total * disk_pct / 100, 2)
    
    return {
        "cpu_pct": cpu,
        "mem_used_mb": mem_used,
        "mem_total_mb": mem_total,
        "mem_pct": mem_pct,
        "disk_used_gb": disk_used,
        "disk_total_gb": disk_total,
        "disk_pct": disk_pct,
        "int_ip": f"192.168.1.{random.randint(10, 250)}",
        "kernel_name": "Linux",
        "kernel_version": "5.15.0",
        "collected_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def send_metrics(scenario, host_key):
    """Send metrics to API"""
    metrics = generate_metrics(scenario)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {host_key}"
    }
    
    try:
        response = requests.post(API_URL, json=metrics, headers=headers, timeout=10)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

def print_summary(scenario, metrics, success, result):
    """Print formatted summary"""
    print(f"\n{'='*60}")
    print(f"Scenario: {scenario.upper()}")
    print(f"Host: {SCENARIOS[scenario]['host_name']}")
    print(f"{'='*60}")
    print(f"CPU: {metrics['cpu_pct']}%")
    print(f"Memory: {metrics['mem_used_mb']}/{metrics['mem_total_mb']} MB ({metrics['mem_pct']}%)")
    print(f"Disk: {metrics['disk_used_gb']}/{metrics['disk_total_gb']} GB ({metrics['disk_pct']}%)")
    print(f"IP: {metrics['int_ip']}")
    
    if success:
        print(f"\n✓ SUCCESS - Data ID: {result.get('data_id')}")
    else:
        print(f"\n✗ FAILED - {result}")
    print(f"{'='*60}")

def main():
    """Main test routine"""
    print("\n" + "="*60)
    print("MONITORING SYSTEM - TEST DATA GENERATOR")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"\nThis will generate test data for {len(SCENARIOS)} simulated hosts")
    print("="*60)
    
    # Option 1: Send once for each scenario
    print("\n[1] Sending one sample from each scenario...\n")
    
    for scenario, config in SCENARIOS.items():
        metrics = generate_metrics(scenario)
        success, result = send_metrics(scenario, config["host_key"])
        print_summary(scenario, metrics, success, result)
        time.sleep(0.5)  # Small delay between requests
    
    # Option 2: Continuous monitoring simulation
    print("\n" + "="*60)
    choice = input("\nContinue with continuous simulation? (y/n): ")
    
    if choice.lower() == 'y':
        print("\n[2] Running continuous simulation (Press Ctrl+C to stop)...\n")
        print("Sending data every 10 seconds...")
        
        try:
            iteration = 1
            while True:
                print(f"\n--- Iteration {iteration} ---")
                for scenario, config in SCENARIOS.items():
                    metrics = generate_metrics(scenario)
                    success, result = send_metrics(scenario, config["host_key"])
                    
                    if success:
                        print(f"✓ {config['host_name']}: CPU={metrics['cpu_pct']}%, "
                              f"Mem={metrics['mem_pct']}%, Disk={metrics['disk_pct']}%")
                    else:
                        print(f"✗ {config['host_name']}: Failed - {result}")
                
                iteration += 1
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n\n✓ Simulation stopped by user")
    
    print("\n" + "="*60)
    print("Test complete! Check your database for the inserted data.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
