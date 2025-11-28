#!/bin/bash
# Client Setup Script
# This script helps set up the client-side agent

echo "=========================================="
echo "Monitoring System - Client Setup"
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
pip install requests psutil
echo "✓ Dependencies installed"

# Check or create agent config
if [ ! -f "agent_config.json" ]; then
    echo ""
    echo "Creating agent_config.json from template..."
    if [ -f "agent_config.json.template" ]; then
        cp agent_config.json.template agent_config.json
        echo "✓ agent_config.json created"
        echo ""
        echo "⚠️  IMPORTANT: Edit agent_config.json with your settings:"
        echo "   - api_url: Your server's IP address and port"
        echo "   - host_key: Unique key (must match database)"
    else
        echo "❌ agent_config.json.template not found"
    fi
else
    echo "✓ agent_config.json found"
fi

# Test system metrics collection
echo ""
echo "Testing system metrics collection..."
python3 -c "
import psutil
try:
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    print(f'✓ CPU: {cpu}%')
    print(f'✓ Memory: {mem.used//(1024**2)}MB / {mem.total//(1024**2)}MB ({mem.percent}%)')
    print(f'✓ Disk: {disk.used//(1024**3)}GB / {disk.total//(1024**3)}GB ({disk.percent}%)')
except Exception as e:
    print(f'❌ Error collecting metrics: {e}')
"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit agent_config.json with your server URL and host_key"
echo "2. Ensure host is registered in database on server"
echo "3. Test agent: python3 agent.py"
echo "4. Set up cron/scheduler for automatic runs"
echo ""

