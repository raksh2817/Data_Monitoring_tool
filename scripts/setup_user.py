#!/usr/bin/env python3
"""
Setup User Script - Creates initial user for the monitoring dashboard
Usage: python setup_user.py <username> <password>
"""

import sys
import getpass
import pymysql
import yaml
from werkzeug.security import generate_password_hash
from pathlib import Path

def load_config():
    """Load configuration from config.yaml"""
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / "config.yaml"
    
    if not config_path.exists():
        print(f"Error: config.yaml not found at {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_user(username: str, password: str):
    """Create a new user in the database"""
    config = load_config()
    
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
    
    # Hash the password
    password_hash = generate_password_hash(password)
    
    conn = None
    try:
        conn = pymysql.connect(**db_config)
        
        with conn.cursor() as cur:
            # Check if users table exists, if not create it
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
            
            # Check if user already exists
            cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            existing = cur.fetchone()
            
            if existing:
                # Update existing user
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, is_active = 1, updated_at = NOW()
                    WHERE username = %s
                """, (password_hash, username))
                print(f"OK Updated user '{username}' successfully")
            else:
                # Create new user
                cur.execute("""
                    INSERT INTO users (username, password_hash, is_active)
                    VALUES (%s, %s, 1)
                """, (username, password_hash))
                print(f"OK Created user '{username}' successfully")
            
            conn.commit()
            
    except pymysql.err.IntegrityError as e:
        conn.rollback()
        print(f"Error: User '{username}' already exists or database constraint violation")
        sys.exit(1)
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if conn:
            conn.close()

def main():
    if len(sys.argv) == 3:
        username = sys.argv[1]
        password = sys.argv[2]
    elif len(sys.argv) == 2:
        username = sys.argv[1]
        password = getpass.getpass("Enter password: ")
    else:
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
    
    if not username or not password:
        print("Error: Username and password are required")
        sys.exit(1)
    
    if len(password) < 6:
        response = input("Warning: Password is less than 6 characters. Continue? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    create_user(username, password)
    print(f"\nUser setup complete! You can now log in with username: {username}")

if __name__ == "__main__":
    main()

