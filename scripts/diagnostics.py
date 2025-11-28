#!/usr/bin/env python3
"""
Diagnostic Script - Tests connectivity and configuration
Run this to diagnose issues with the monitoring system
"""

import sys
import socket
import json
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_imports():
    """Test if required packages are installed"""
    print_section("Testing Python Packages")
    
    packages = {
        'requests': 'HTTP client for API calls',
        'psutil': 'System metrics collection',
        'pymysql': 'MySQL database connection (server only)',
        'flask': 'Web framework (server only)',
        'pydantic': 'Data validation (server only)',
        'yaml': 'Config file parsing (server only)'
    }
    
    all_ok = True
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✓ {package:15s} - {description}")
        except ImportError:
            print(f"✗ {package:15s} - NOT INSTALLED - {description}")
            all_ok = False
    
    return all_ok

def test_config_files():
    """Check if configuration files exist"""
    print_section("Checking Configuration Files")
    
    files = {
        'agent_config.json': 'Agent configuration',
        'config.yaml': 'Flask server configuration',
        'db_fixed.sql': 'Database schema'
    }
    
    for filename, description in files.items():
        path = Path(filename)
        if path.exists():
            print(f"✓ {filename:20s} - {description}")
            if filename == 'agent_config.json':
                try:
                    with open(path) as f:
                        config = json.load(f)
                    print(f"    API URL: {config.get('api_url')}")
                    print(f"    Host Key: {config.get('host_key', '')[:10]}... (masked)")
                except Exception as e:
                    print(f"    ⚠ Error reading config: {e}")
        else:
            print(f"✗ {filename:20s} - NOT FOUND - {description}")

def test_network_connectivity(host, port):
    """Test if a host:port is reachable"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"    Error: {e}")
        return False

def test_api_connectivity():
    """Test connection to Flask API"""
    print_section("Testing API Connectivity")
    
    # Try to load agent config
    config_path = Path('agent_config.json')
    if not config_path.exists():
        print("✗ agent_config.json not found")
        print("  Run agent.py once to create default config")
        return False
    
    try:
        with open(config_path) as f:
            config = json.load(f)
        api_url = config.get('api_url', 'http://localhost:5000/report')
    except Exception as e:
        print(f"✗ Error reading config: {e}")
        return False
    
    # Parse URL
    print(f"Testing: {api_url}")
    
    # Extract host and port
    try:
        from urllib.parse import urlparse
        parsed = urlparse(api_url)
        host = parsed.hostname or 'localhost'
        port = parsed.port or (443 if parsed.scheme == 'https' else 5000)
        
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        
        # Test connection
        if test_network_connectivity(host, port):
            print(f"✓ Port {port} is reachable on {host}")
        else:
            print(f"✗ Cannot reach port {port} on {host}")
            print(f"  - Check if Flask server is running")
            print(f"  - Check firewall rules")
            print(f"  - Verify the URL in agent_config.json")
            return False
        
        # Try HTTP request
        try:
            import requests
            health_url = f"{parsed.scheme}://{host}:{port}/health"
            print(f"\nTesting health endpoint: {health_url}")
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print(f"✓ Health check passed: {response.json()}")
                return True
            else:
                print(f"✗ Health check failed: {response.status_code}")
                return False
        except ImportError:
            print("  (requests not installed, skipping HTTP test)")
            return True
        except Exception as e:
            print(f"✗ HTTP request failed: {e}")
            return False
            
    except Exception as e:
        print(f"✗ Error parsing URL: {e}")
        return False

def test_database_connectivity():
    """Test connection to MySQL database (server-side check)"""
    print_section("Testing Database Connectivity (Server Only)")
    
    try:
        import pymysql
    except ImportError:
        print("✗ pymysql not installed (this is OK if you're running on agent machine)")
        return None
    
    try:
        import yaml
        config_path = Path('config.yaml')
        if not config_path.exists():
            print("✗ config.yaml not found")
            return False
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        db_config = config.get('database', {})
        print(f"Testing connection to: {db_config.get('host')}")
        print(f"Database: {db_config.get('name')}")
        print(f"User: {db_config.get('user')}")
        
        conn = pymysql.connect(
            host=db_config.get('host'),
            port=db_config.get('port', 3306),
            user=db_config.get('user'),
            password=db_config.get('password'),
            database=db_config.get('name'),
            connect_timeout=10
        )
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        print("✓ Database connection successful")
        
        # Check tables
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
        print(f"\nFound {len(tables)} tables:")
        expected_tables = ['hosts', 'incoming_data', 'alert_types', 'alerts', 'host_alert_checks']
        for table in expected_tables:
            if table in tables:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (missing - run db_fixed.sql)")
        
        conn.close()
        return True
        
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        return False
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_system_metrics():
    """Test if we can collect system metrics"""
    print_section("Testing System Metrics Collection")
    
    try:
        import psutil
    except ImportError:
        print("✗ psutil not installed")
        print("  Install with: pip install psutil --break-system-packages")
        return False
    
    try:
        cpu = psutil.cpu_percent(interval=1)
        print(f"✓ CPU usage: {cpu}%")
        
        mem = psutil.virtual_memory()
        print(f"✓ Memory: {mem.used//(1024**2)}MB / {mem.total//(1024**2)}MB ({mem.percent}%)")
        
        disk = psutil.disk_usage('/')
        print(f"✓ Disk: {disk.used//(1024**3)}GB / {disk.total//(1024**3)}GB ({disk.percent}%)")
        
        hostname = socket.gethostname()
        print(f"✓ Hostname: {hostname}")
        
        return True
    except Exception as e:
        print(f"✗ Error collecting metrics: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print(f"\n{'#'*60}")
    print("#  Monitoring System Diagnostics")
    print(f"{'#'*60}")
    
    results = {
        'Packages': test_imports(),
        'Config Files': test_config_files(),
        'API Connectivity': test_api_connectivity(),
        'Database': test_database_connectivity(),
        'System Metrics': test_system_metrics()
    }
    
    print_section("Summary")
    
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"{status:8s} - {test_name}")
    
    # Overall status
    failures = sum(1 for r in results.values() if r is False)
    if failures == 0:
        print("\n✓ All critical tests passed!")
        return 0
    else:
        print(f"\n✗ {failures} test(s) failed")
        print("  See above for details and solutions")
        return 1

if __name__ == "__main__":
    sys.exit(main())
