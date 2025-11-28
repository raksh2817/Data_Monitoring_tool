#!/usr/bin/env python3
"""
Alert Checker - Monitors incoming data and triggers alerts based on thresholds
Run this periodically (e.g., via cron every minute) to check for alert conditions
"""

import pymysql
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# Load database configuration
with open('config.yaml') as f:
    config = yaml.safe_load(f)

DB_CONFIG = {
    'host': config['database']['host'],
    'user': config['database']['user'],
    'password': config['database']['password'],
    'database': config['database']['name'],
    'charset': config['database']['charset'],
}

# ============================================================================
# ALERT CHECK FUNCTIONS
# ============================================================================
# Each function returns (alert_triggered: bool, message: str)

def check_host_online(conn, host_id: int, params: dict) -> Tuple[bool, str]:
    """
    Check if host has reported recently
    params: {"offline_threshold_minutes": 60}
    """
    threshold_minutes = params.get('offline_threshold_minutes', 60)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT MAX(collected_at) as last_seen, h.host_name
            FROM incoming_data i
            JOIN hosts h ON i.host_id = h.host_id
            WHERE i.host_id = %s
            GROUP BY h.host_name
        """, (host_id,))
        result = cur.fetchone()
    
    if not result or not result['last_seen']:
        return True, f"Host has never reported data"
    
    last_seen = result['last_seen']
    host_name = result['host_name']
    threshold = datetime.now() - timedelta(minutes=threshold_minutes)
    
    if last_seen < threshold:
        minutes_ago = int((datetime.now() - last_seen).total_seconds() / 60)
        return True, f"Host '{host_name}' offline for {minutes_ago} minutes (threshold: {threshold_minutes})"
    
    return False, f"Host '{host_name}' is online"

def check_disk_space(conn, host_id: int, params: dict) -> Tuple[bool, str]:
    """
    Check if disk usage exceeds threshold
    params: {"threshold_pct": 90}
    """
    threshold_pct = params.get('threshold_pct', 90)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT disk_pct, h.host_name
            FROM incoming_data i
            JOIN hosts h ON i.host_id = h.host_id
            WHERE i.host_id = %s
            ORDER BY i.collected_at DESC
            LIMIT 1
        """, (host_id,))
        result = cur.fetchone()
    
    if not result or result['disk_pct'] is None:
        return False, "No disk data available"
    
    disk_pct = float(result['disk_pct'])
    host_name = result['host_name']
    
    if disk_pct >= threshold_pct:
        return True, f"Host '{host_name}' disk usage critical: {disk_pct}% (threshold: {threshold_pct}%)"
    
    return False, f"Host '{host_name}' disk usage normal: {disk_pct}%"

def check_memory_usage(conn, host_id: int, params: dict) -> Tuple[bool, str]:
    """
    Check if memory usage exceeds threshold
    params: {"threshold_pct": 90}
    """
    threshold_pct = params.get('threshold_pct', 90)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT mem_pct, h.host_name
            FROM incoming_data i
            JOIN hosts h ON i.host_id = h.host_id
            WHERE i.host_id = %s
            ORDER BY i.collected_at DESC
            LIMIT 1
        """, (host_id,))
        result = cur.fetchone()
    
    if not result or result['mem_pct'] is None:
        return False, "No memory data available"
    
    mem_pct = float(result['mem_pct'])
    host_name = result['host_name']
    
    if mem_pct >= threshold_pct:
        return True, f"Host '{host_name}' memory usage critical: {mem_pct}% (threshold: {threshold_pct}%)"
    
    return False, f"Host '{host_name}' memory usage normal: {mem_pct}%"

def check_cpu_usage(conn, host_id: int, params: dict) -> Tuple[bool, str]:
    """
    Check if CPU usage exceeds threshold
    params: {"threshold_pct": 90}
    """
    threshold_pct = params.get('threshold_pct', 90)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT cpu_pct, h.host_name
            FROM incoming_data i
            JOIN hosts h ON i.host_id = h.host_id
            WHERE i.host_id = %s
            ORDER BY i.collected_at DESC
            LIMIT 1
        """, (host_id,))
        result = cur.fetchone()
    
    if not result or result['cpu_pct'] is None:
        return False, "No CPU data available"
    
    cpu_pct = float(result['cpu_pct'])
    host_name = result['host_name']
    
    if cpu_pct >= threshold_pct:
        return True, f"Host '{host_name}' CPU usage critical: {cpu_pct}% (threshold: {threshold_pct}%)"
    
    return False, f"Host '{host_name}' CPU usage normal: {cpu_pct}%"

# Map function names to actual functions
ALERT_FUNCTIONS = {
    'check_host_online': check_host_online,
    'check_disk_space': check_disk_space,
    'check_memory_usage': check_memory_usage,
    'check_cpu_usage': check_cpu_usage,
}

# ============================================================================
# ALERT STATE MANAGEMENT
# ============================================================================

def get_active_hosts(conn) -> List[Dict]:
    """Get all active hosts"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT host_id, host_name, last_seen
            FROM hosts
            WHERE is_active = 1
            ORDER BY host_id
        """)
        return cur.fetchall()

def get_host_alert_checks(conn, host_id: int) -> List[Dict]:
    """Get all enabled alert checks for a host"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                hac.association_id,
                hac.check_id,
                hac.params_json,
                at.check_name,
                at.check_key,
                at.function_name,
                at.params_json as default_params,
                at.severity
            FROM host_alert_checks hac
            JOIN alert_types at ON hac.check_id = at.check_id
            WHERE hac.host_id = %s AND hac.enabled = 1 AND at.enabled = 1
        """, (host_id,))
        return cur.fetchall()

def get_last_alert_state(conn, host_id: int, check_id: int) -> Optional[str]:
    """Get the most recent alert status for this host/check combination"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT status
            FROM alerts
            WHERE host_id = %s AND check_id = %s
            ORDER BY triggered_at DESC
            LIMIT 1
        """, (host_id, check_id))
        result = cur.fetchone()
        return result['status'] if result else None

def create_alert(conn, host_id: int, check_id: int, severity: str, message: str, data_id: Optional[int] = None):
    """Create a new alert record"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO alerts (
                host_id, check_id, data_id,
                triggered_at, severity, message, status,
                created_at
            ) VALUES (
                %s, %s, %s, NOW(), %s, %s, 'open', NOW()
            )
        """, (host_id, check_id, data_id, severity, message))
        alert_id = cur.lastrowid
    conn.commit()
    return alert_id

def resolve_alert(conn, host_id: int, check_id: int, message: str):
    """Mark alert as resolved (condition cleared)"""
    with conn.cursor() as cur:
        # Update most recent open alert to resolved
        cur.execute("""
            UPDATE alerts
            SET status = 'resolved', 
                message = CONCAT(message, ' → RESOLVED: ', %s),
                updated_at = NOW()
            WHERE host_id = %s 
              AND check_id = %s 
              AND status = 'open'
            ORDER BY triggered_at DESC
            LIMIT 1
        """, (message, host_id, check_id))
    conn.commit()

# ============================================================================
# MAIN ALERT CHECKING LOGIC
# ============================================================================

def check_alerts_for_host(conn, host: Dict) -> Dict:
    """
    Check all alerts for a single host
    Returns summary of alerts triggered
    """
    host_id = host['host_id']
    host_name = host['host_name']
    
    results = {
        'host_id': host_id,
        'host_name': host_name,
        'checks_run': 0,
        'alerts_triggered': 0,
        'alerts_resolved': 0,
        'details': []
    }
    
    # Get all alert checks for this host
    checks = get_host_alert_checks(conn, host_id)
    
    if not checks:
        results['details'].append(f"No alert checks configured for {host_name}")
        return results
    
    for check in checks:
        check_id = check['check_id']
        check_name = check['check_name']
        function_name = check['function_name']
        severity = check['severity']
        
        # Merge default params with host-specific params
        params = json.loads(check['default_params']) if check['default_params'] else {}
        if check['params_json']:
            host_params = json.loads(check['params_json'])
            params.update(host_params)
        
        # Run the check function
        if function_name not in ALERT_FUNCTIONS:
            results['details'].append(f"❌ Unknown function: {function_name}")
            continue
        
        check_function = ALERT_FUNCTIONS[function_name]
        results['checks_run'] += 1
        
        try:
            # Execute the check
            alert_triggered, message = check_function(conn, host_id, params)
            
            # Get previous state
            last_state = get_last_alert_state(conn, host_id, check_id)
            
            # State change logic
            if alert_triggered:
                # Alert condition is TRUE
                if last_state != 'open':
                    # State changed: normal → alert OR resolved → alert
                    alert_id = create_alert(conn, host_id, check_id, severity, message)
                    results['alerts_triggered'] += 1
                    results['details'].append(f"🚨 NEW ALERT #{alert_id}: {check_name} - {message}")
                else:
                    # Still in alert state, no change
                    results['details'].append(f"⚠️  ONGOING: {check_name} - {message}")
            else:
                # Alert condition is FALSE (normal)
                if last_state == 'open':
                    # State changed: alert → normal
                    resolve_alert(conn, host_id, check_id, message)
                    results['alerts_resolved'] += 1
                    results['details'].append(f"✅ RESOLVED: {check_name} - {message}")
                else:
                    # Still normal, no change
                    results['details'].append(f"✓  OK: {check_name} - {message}")
        
        except Exception as e:
            results['details'].append(f"❌ ERROR in {check_name}: {str(e)}")
    
    return results

def main():
    """Main alert checking routine"""
    print("\n" + "="*70)
    print(f"ALERT CHECKER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    conn = None
    try:
        # Connect to database
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        print("✓ Connected to database")
        
        # Get all active hosts
        hosts = get_active_hosts(conn)
        print(f"✓ Found {len(hosts)} active host(s)\n")
        
        if not hosts:
            print("No active hosts to check.")
            return
        
        # Check alerts for each host
        total_triggered = 0
        total_resolved = 0
        total_checks = 0
        
        for host in hosts:
            print(f"\n{'─'*70}")
            print(f"Checking host: {host['host_name']} (ID: {host['host_id']})")
            print(f"{'─'*70}")
            
            results = check_alerts_for_host(conn, host)
            total_checks += results['checks_run']
            total_triggered += results['alerts_triggered']
            total_resolved += results['alerts_resolved']
            
            for detail in results['details']:
                print(f"  {detail}")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Hosts checked: {len(hosts)}")
        print(f"Checks run: {total_checks}")
        print(f"New alerts: {total_triggered}")
        print(f"Resolved alerts: {total_resolved}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
