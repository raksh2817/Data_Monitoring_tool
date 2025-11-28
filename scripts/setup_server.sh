#!/bin/bash
# Server Setup Script
# This script helps set up the server-side components

echo "=========================================="
echo "Monitoring System - Server Setup"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi
echo "✓ Python 3 found: $(python3 --version)"

# Check pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed"
    exit 1
fi
echo "✓ pip3 found"

# Create virtual environment if it doesn't exist
if [ ! -d "../.venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv ../.venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source ../.venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Check config file
if [ ! -f "config.yaml" ]; then
    echo ""
    echo "⚠️  config.yaml not found!"
    echo "Please create config.yaml with your database settings"
    echo "See README.md for configuration details"
else
    echo "✓ config.yaml found"
fi

# Check database connection
echo ""
echo "Testing database connection..."
python3 -c "
import yaml
import pymysql
try:
    with open('config.yaml') as f:
        config = yaml.safe_load(f)
    db = config['database']
    conn = pymysql.connect(
        host=db['host'],
        port=db['port'],
        user=db['user'],
        password=db['password'],
        database=db['name'],
        connect_timeout=5
    )
    conn.close()
    print('✓ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('Please check your config.yaml settings')
"

# Check templates
if [ ! -d "templates" ]; then
    echo ""
    echo "⚠️  templates/ directory not found!"
    echo "Creating templates directory..."
    mkdir -p templates
    echo "✓ templates/ directory created"
    echo "Please copy template files to templates/"
else
    echo "✓ templates/ directory found"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Ensure config.yaml is configured correctly"
echo "2. Run database setup: mysql < db_fixed.sql"
echo "3. Start server: python3 app_new.py"
echo ""

