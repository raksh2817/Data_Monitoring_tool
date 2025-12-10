#!/usr/bin/env python3
"""
Database Setup Script - Creates all required tables for the monitoring system
Usage: python setup_database.py [--drop-existing]
"""

import sys
import argparse
from pathlib import Path

import pymysql
import yaml


def load_config():
    """Load configuration from config.yaml"""
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / "config.yaml"
    
    if not config_path.exists():
        print(f"ERROR: config.yaml not found at {config_path}")
        print("Please create config.yaml with your database settings")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_db_connection(config):
    """Create database connection"""
    db_config = {
        'host': config['database']['host'],
        'port': int(config['database']['port']),
        'user': config['database']['user'],
        'password': config['database']['password'],
        'database': config['database']['name'],
        'charset': config['database']['charset'],
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': False,
    }
    
    try:
        conn = pymysql.connect(**db_config)
        return conn
    except Exception as e:
        print(f"ERROR: Error connecting to database: {e}")
        print("\nPlease check your config.yaml database settings:")
        print(f"  Host: {db_config['host']}")
        print(f"  Database: {db_config['database']}")
        print(f"  User: {db_config['user']}")
        sys.exit(1)


def setup_database(drop_existing=False):
    """Set up all database tables"""
    print("=" * 70)
    print("Database Setup Script")
    print("=" * 70)
    print()
    
    # Load configuration
    print("Loading configuration...")
    config = load_config()
    print(f"OK Config loaded from {Path(__file__).parent / 'config.yaml'}")
    print()
    
    # Connect to database
    print("Connecting to database...")
    conn = get_db_connection(config)
    print(f"OK Connected to {config['database']['host']}/{config['database']['name']}")
    print()
    
    try:
        with conn.cursor() as cur:
            # Drop tables if requested
            if drop_existing:
                print("WARNING: DROP EXISTING TABLES mode enabled")
                print("Dropping existing tables (if they exist)...")
                drop_order = [
                    'host_alert_checks',
                    'alerts',
                    'alert_types',
                    'incoming_data',
                    'hosts',
                    'users',
                ]
                for table in drop_order:
                    try:
                        cur.execute(f"DROP TABLE IF EXISTS {table}")
                        print(f"  OK Dropped {table} (if existed)")
                    except Exception as e:
                        print(f"  WARNING: Error dropping {table}: {e}")
                conn.commit()
                print()
            
            # Create tables
            print("Creating tables...")
            
            # 1. Users table
            print("  Creating users table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                  user_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
                  username VARCHAR(100) NOT NULL,
                  password_hash VARCHAR(255) NOT NULL,
                  is_active TINYINT(1) NOT NULL DEFAULT 1,
                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                  
                  PRIMARY KEY (user_id),
                  UNIQUE KEY uq_username (username)
                ) ENGINE=InnoDB
                  DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
            """)
            print("    OK users table created/verified")
            
            # 2. Hosts table
            print("  Creating hosts table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS hosts (
                  host_id    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                  host_name  VARCHAR(255)    NOT NULL,
                  host_key   VARCHAR(64)     NOT NULL,
                  os_name    VARCHAR(100)    NULL,
                  os_version VARCHAR(50)     NULL,
                  is_active  TINYINT(1)      NOT NULL DEFAULT 1,
                  last_seen  DATETIME        NULL,
                  created_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  
                  PRIMARY KEY (host_id),
                  UNIQUE KEY uq_host_name (host_name),
                  UNIQUE KEY uq_host_key (host_key),
                  KEY ix_last_seen (last_seen)
                ) ENGINE=InnoDB
                  DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
            """)
            print("    OK hosts table created/verified")
            
            # 3. Incoming data table
            print("  Creating incoming_data table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS incoming_data (
                  data_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                  host_id         BIGINT UNSIGNED NOT NULL,
                  collected_at    DATETIME(3)     NOT NULL,
                  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  
                  int_ip          VARCHAR(45)     NULL,
                  public_ip       VARCHAR(45)     NULL,
                  kernel_name     VARCHAR(50)     NULL,
                  kernel_version  VARCHAR(50)     NULL,
                  
                  cpu_pct         DECIMAL(5,2)    NULL,
                  mem_used_mb     INT UNSIGNED    NULL,
                  mem_total_mb    INT UNSIGNED    NULL,
                  mem_pct         DECIMAL(5,2)    NULL,
                  disk_used_gb    DECIMAL(10,2)   NULL,
                  disk_total_gb   DECIMAL(10,2)   NULL,
                  disk_pct        DECIMAL(5,2)    NULL,
                  
                  dataset_name    VARCHAR(200)    NULL,
                  partition_key   VARCHAR(200)    NULL,
                  files_count     INT UNSIGNED    NULL,
                  size_bytes      BIGINT UNSIGNED NULL,
                  min_event_ts    DATETIME        NULL,
                  max_event_ts    DATETIME        NULL,
                  extra           JSON            NULL,
                  
                  PRIMARY KEY (data_id),
                  KEY ix_host_time (host_id, collected_at),
                  KEY ix_dataset_time (dataset_name, partition_key, collected_at),
                  KEY ix_collected_at (collected_at),
                  
                  CONSTRAINT fk_incoming_host
                    FOREIGN KEY (host_id) REFERENCES hosts(host_id)
                    ON DELETE CASCADE
                ) ENGINE=InnoDB
                  DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
            """)
            print("    OK incoming_data table created/verified")
            
            # 4. Alert types table
            print("  Creating alert_types table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alert_types (
                  check_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                  check_name       VARCHAR(120)    NOT NULL,
                  check_key        VARCHAR(64)     NOT NULL,
                  function_name    VARCHAR(100)    NULL,
                  params_json      JSON            NULL,
                  severity         ENUM('L1','L2','L3') NOT NULL DEFAULT 'L1',
                  cooldown_minutes INT UNSIGNED    NOT NULL DEFAULT 60,
                  enabled          TINYINT(1)      NOT NULL DEFAULT 1,
                  notes            VARCHAR(500)    NULL,
                  created_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                         ON UPDATE CURRENT_TIMESTAMP,
                  
                  PRIMARY KEY (check_id),
                  UNIQUE KEY uq_check_name (check_name),
                  UNIQUE KEY uq_check_key  (check_key)
                ) ENGINE=InnoDB
                  DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
            """)
            print("    OK alert_types table created/verified")
            
            # 5. Alerts table
            print("  Creating alerts table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                  alert_id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                  host_id         BIGINT UNSIGNED NOT NULL,
                  check_id        BIGINT UNSIGNED NOT NULL,
                  data_id         BIGINT UNSIGNED NULL,
                  triggered_at    DATETIME        NOT NULL,
                  severity        ENUM('L1','L2','L3') NOT NULL,
                  message         VARCHAR(1000)   NULL,
                  status          ENUM('open','acknowledged','resolved')
                                        NOT NULL DEFAULT 'open',
                  last_notified_at DATETIME       NULL,
                  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,
                  
                  PRIMARY KEY (alert_id),
                  KEY ix_host_status (host_id, status),
                  KEY ix_check_status (check_id, status),
                  KEY ix_triggered_at (triggered_at),
                  
                  CONSTRAINT fk_alert_host
                    FOREIGN KEY (host_id) REFERENCES hosts(host_id)
                    ON DELETE CASCADE,
                  
                  CONSTRAINT fk_alert_check
                    FOREIGN KEY (check_id) REFERENCES alert_types(check_id)
                    ON DELETE RESTRICT,
                  
                  CONSTRAINT fk_alert_data
                    FOREIGN KEY (data_id) REFERENCES incoming_data(data_id)
                    ON DELETE SET NULL
                ) ENGINE=InnoDB
                  DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
            """)
            print("    OK alerts table created/verified")
            
            # 6. Host alert checks table
            print("  Creating host_alert_checks table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS host_alert_checks (
                  association_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                  host_id BIGINT UNSIGNED NOT NULL,
                  check_id BIGINT UNSIGNED NOT NULL,
                  enabled TINYINT(1) DEFAULT 1,
                  params_json JSON,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                  
                  UNIQUE KEY uq_host_check (host_id, check_id),
                  FOREIGN KEY (host_id) REFERENCES hosts(host_id) ON DELETE CASCADE,
                  FOREIGN KEY (check_id) REFERENCES alert_types(check_id) ON DELETE CASCADE
                ) ENGINE=InnoDB
                  DEFAULT CHARSET=utf8mb4
                  COLLATE=utf8mb4_unicode_ci
            """)
            print("    OK host_alert_checks table created/verified")
            
            conn.commit()
            print()
            
            # Insert default alert types (only if they don't exist)
            print("Setting up default alert types...")
            cur.execute("SELECT COUNT(*) as count FROM alert_types")
            existing_count = cur.fetchone()['count']
            
            if existing_count == 0:
                cur.execute("""
                    INSERT INTO alert_types (check_name, check_key, function_name, params_json, severity, notes) VALUES
                    ('Host Online', 'host_online', 'check_host_online', '{"offline_threshold_minutes": 60}', 'L1', 'Checks if host has sent data recently'),
                    ('Disk Space', 'disk_space', 'check_disk_space', '{"threshold_pct": 90}', 'L2', 'Alerts when disk usage exceeds threshold'),
                    ('Memory Usage', 'memory_usage', 'check_memory_usage', '{"threshold_pct": 90}', 'L2', 'Alerts when memory usage exceeds threshold'),
                    ('CPU Usage', 'cpu_usage', 'check_cpu_usage', '{"threshold_pct": 90}', 'L2', 'Alerts when CPU usage exceeds threshold')
                """)
                conn.commit()
                print("  OK Inserted 4 default alert types")
            else:
                print(f"  INFO: {existing_count} alert types already exist, skipping insert")
            
            print()
            
            # Show table summary
            print("Database Summary:")
            cur.execute("SHOW TABLES")
            tables = [list(row.values())[0] for row in cur.fetchall()]
            for table in sorted(tables):
                cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cur.fetchone()['count']
                print(f"  • {table}: {count} rows")
            
            print()
            print("=" * 70)
            print("SUCCESS: Database setup complete!")
            print("=" * 70)
            print()
            print("Next steps:")
            print("  1. Create a user account: python setup_user.py <username> <password>")
            print("  2. Start the Flask server: python app_new.py")
            print()
            
    except pymysql.err.Error as e:
        conn.rollback()
        print()
        print(f"ERROR: Database error: {e}")
        sys.exit(1)
    except Exception as e:
        conn.rollback()
        print()
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Set up database tables for the monitoring system'
    )
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop existing tables before creating new ones (WARNING: This will delete all data!)'
    )
    
    args = parser.parse_args()
    
    if args.drop_existing:
        response = input("WARNING: This will DELETE ALL DATA in existing tables! Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)
    
    setup_database(drop_existing=args.drop_existing)


if __name__ == "__main__":
    main()

