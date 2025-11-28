#!/usr/bin/env python3
"""
Alert System Demo - Shows alert triggering and resolution
This script sends metrics that will trigger alerts, then normal metrics to resolve them
"""

import requests
import time
from datetime import datetime

API_URL = "http://localhost:5000/report"

def send_metrics(host_key, host_name, cpu, mem, disk, description):
    """Send metrics to API"""
    metrics = {
        "cpu_pct": cpu,
        "mem_pct": mem,
        "disk_pct": disk,
        "mem_used_mb": int(16384 * mem / 100),
        "mem_total_mb": 16384,
        "disk_used_gb": round(500 * disk / 100, 2),
        "disk_total_gb": 500.0,
        "int_ip": "192.168.1.100",
        "kernel_name": "Linux",
        "kernel_version": "5.15.0",
        "collected_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # FIX: Add timestamp
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {host_key}"
    }
    
    try:
        response = requests.post(API_URL, json=metrics, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"✓ {host_name}: {description}")
            print(f"  CPU={cpu}%, Mem={mem}%, Disk={disk}%")
            return True
        else:
            print(f"✗ {host_name}: Failed - {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ {host_name}: Error - {e}")
        return False

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def main():
    """Demonstrate alert triggering and resolution"""
    
    print_section("ALERT SYSTEM DEMONSTRATION")
    
    scenarios = [
        {
            "name": "storage-server-04",
            "key": "high-disk-server",
            "description": "High Disk Scenario",
            "normal": {"cpu": 15, "mem": 30, "disk": 45},
            "alert": {"cpu": 15, "mem": 30, "disk": 92},  # Will trigger disk alert
        },
        {
            "name": "db-server-03",
            "key": "high-mem-server",
            "description": "High Memory Scenario",
            "normal": {"cpu": 20, "mem": 50, "disk": 40},
            "alert": {"cpu": 20, "mem": 93, "disk": 40},  # Will trigger memory alert
        },
    ]
    
    # ========================================================================
    # Step 1: Send normal metrics
    # ========================================================================
    print_section("STEP 1: Sending Normal Metrics")
    print("These should NOT trigger any alerts\n")
    
    for scenario in scenarios:
        send_metrics(
            scenario["key"],
            scenario["name"],
            scenario["normal"]["cpu"],
            scenario["normal"]["mem"],
            scenario["normal"]["disk"],
            f"{scenario['description']} - Normal state"
        )
        time.sleep(0.5)
    
    print("\n⏸️  Waiting 2 seconds...")
    time.sleep(2)
    
    # ========================================================================
    # Step 2: Run alert checker (first time - should be all OK)
    # ========================================================================
    print_section("STEP 2: Running Alert Checker")
    print("Expected: All checks OK, no alerts\n")
    print("→ Run: python check_alerts.py")
    print("   (Check output above for results)")
    
    input("\n[Press Enter to continue to alert triggering phase...]")
    
    # ========================================================================
    # Step 3: Send metrics that trigger alerts
    # ========================================================================
    print_section("STEP 3: Sending Critical Metrics")
    print("These WILL trigger alerts\n")
    
    for scenario in scenarios:
        send_metrics(
            scenario["key"],
            scenario["name"],
            scenario["alert"]["cpu"],
            scenario["alert"]["mem"],
            scenario["alert"]["disk"],
            f"{scenario['description']} - CRITICAL STATE"
        )
        time.sleep(0.5)
    
    print("\n⏸️  Waiting 2 seconds...")
    time.sleep(2)
    
    # ========================================================================
    # Step 4: Run alert checker (should trigger new alerts)
    # ========================================================================
    print_section("STEP 4: Running Alert Checker Again")
    print("Expected: NEW ALERTS triggered!\n")
    print("→ Run: python check_alerts.py")
    print("   (You should see 🚨 NEW ALERT messages)")
    
    input("\n[Press Enter to continue to alert resolution phase...]")
    
    # ========================================================================
    # Step 5: Send normal metrics again (resolve alerts)
    # ========================================================================
    print_section("STEP 5: Sending Normal Metrics Again")
    print("These will resolve the alerts\n")
    
    for scenario in scenarios:
        send_metrics(
            scenario["key"],
            scenario["name"],
            scenario["normal"]["cpu"],
            scenario["normal"]["mem"],
            scenario["normal"]["disk"],
            f"{scenario['description']} - Back to normal"
        )
        time.sleep(0.5)
    
    print("\n⏸️  Waiting 2 seconds...")
    time.sleep(2)
    
    # ========================================================================
    # Step 6: Run alert checker (should resolve alerts)
    # ========================================================================
    print_section("STEP 6: Running Alert Checker Final Time")
    print("Expected: Alerts RESOLVED!\n")
    print("→ Run: python check_alerts.py")
    print("   (You should see ✅ RESOLVED messages)")
    
    # ========================================================================
    # Summary
    # ========================================================================
    print_section("DEMONSTRATION COMPLETE")
    
    print("What just happened:")
    print("1. ✓ Sent normal metrics → No alerts")
    print("2. 🚨 Sent critical metrics → Alerts triggered")
    print("3. ✅ Sent normal metrics → Alerts resolved\n")
    
    print("This demonstrates:")
    print("• State-change detection (only alerts on transitions)")
    print("• Multiple alert types (disk, memory)")
    print("• Alert resolution when conditions normalize")
    print("• Per-host configurable thresholds\n")
    
    print("View alerts in database:")
    print("  mysql -h mysql.clarksonmsda.org -u srinatr -p -e \"")
    print("    USE srinatr_monitor;")
    print("    SELECT ")
    print("      a.alert_id,")
    print("      h.host_name,")
    print("      at.check_name,")
    print("      a.severity,")
    print("      a.status,")
    print("      a.triggered_at,")
    print("      a.message")
    print("    FROM alerts a")
    print("    JOIN hosts h ON a.host_id = h.host_id")
    print("    JOIN alert_types at ON a.check_id = at.check_id")
    print("    ORDER BY a.triggered_at DESC LIMIT 10;")
    print("  \"")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
