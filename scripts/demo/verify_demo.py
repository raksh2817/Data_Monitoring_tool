#!/usr/bin/env python3
"""
Pre-Demo Verification Script
Run this to make sure everything is ready for your November 26 meeting
"""

import requests
import pymysql
import yaml
from pathlib import Path
import sys

def print_status(test_name, passed, message=""):
    """Print formatted test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status:8s} - {test_name}")
    if message:
        print(f"          {message}")

def test_database_connection():
    """Test database connectivity"""
    try:
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
        
        db = config['database']
        conn = pymysql.connect(
            host=db['host'],
            user=db['user'],
            password=db['password'],
            database=db['name'],
            connect_timeout=10
        )
        
        # Test query
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM hosts WHERE is_active=1")
            count = cur.fetchone()[0]
        
        conn.close()
        return True, f"{count} active hosts in database"
    except Exception as e:
        return False, str(e)

def test_flask_server():
    """Test if Flask is running"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            return True, "Flask server responding"
        else:
            return False, f"Server returned {response.status_code}"
    except Exception as e:
        return False, "Flask server not running - Start with: python app.py"

def test_api_endpoint():
    """Test the /report endpoint"""
    try:
        test_data = {
            "cpu_pct": 10.5,
            "mem_pct": 20.0,
            "disk_pct": 30.0,
            "mem_used_mb": 2048,
            "mem_total_mb": 8192,
            "disk_used_gb": 50.0,
            "disk_total_gb": 100.0
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-key-123"
        }
        
        response = requests.post(
            "http://localhost:5000/report",
            json=test_data,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data_id = response.json().get('data_id')
            return True, f"API working - Data ID: {data_id}"
        else:
            return False, f"API returned {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

def test_required_files():
    """Check if all required files exist"""
    required_files = [
        'app.py',
        'config.yaml',
        'agent.py',
        'test_monitoring.py',
        'db_fixed.sql',
        'setup_test_hosts.sql',
        'DEMO_SCRIPT.md'
    ]
    
    missing = []
    for filename in required_files:
        if not Path(filename).exists():
            missing.append(filename)
    
    if missing:
        return False, f"Missing files: {', '.join(missing)}"
    else:
        return True, f"All {len(required_files)} files present"

def test_data_in_database():
    """Check if there's recent data"""
    try:
        with open('config.yaml') as f:
            config = yaml.safe_load(f)
        
        db = config['database']
        conn = pymysql.connect(
            host=db['host'],
            user=db['user'],
            password=db['password'],
            database=db['name']
        )
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM incoming_data 
                WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            """)
            recent_count = cur.fetchone()[0]
        
        conn.close()
        
        if recent_count > 0:
            return True, f"{recent_count} data points in last hour"
        else:
            return False, "No recent data - Run test_monitoring.py"
    except Exception as e:
        return False, str(e)

def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("PRE-DEMO VERIFICATION")
    print("="*60 + "\n")
    
    tests = [
        ("Required Files", test_required_files),
        ("Database Connection", test_database_connection),
        ("Flask Server", test_flask_server),
        ("API Endpoint", test_api_endpoint),
        ("Recent Data", test_data_in_database),
    ]
    
    results = []
    for test_name, test_func in tests:
        passed, message = test_func()
        print_status(test_name, passed, message)
        results.append(passed)
    
    print("\n" + "="*60)
    passed_count = sum(results)
    total_count = len(results)
    
    if all(results):
        print(f"✓ ALL TESTS PASSED ({passed_count}/{total_count})")
        print("="*60)
        print("\nYou're ready for the demo! 🎉")
        print("\nNext steps:")
        print("  1. Review DEMO_SCRIPT.md")
        print("  2. Practice running through the demo")
        print("  3. Run test_monitoring.py before meeting to ensure fresh data")
        return 0
    else:
        print(f"✗ {total_count - passed_count} TEST(S) FAILED ({passed_count}/{total_count} passed)")
        print("="*60)
        print("\nFix the failed tests before the demo.")
        print("See error messages above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
