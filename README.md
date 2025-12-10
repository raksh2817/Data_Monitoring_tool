# Data Monitoring Tool

A comprehensive system monitoring solution that collects real-time metrics from multiple hosts, stores them in a centralized database, and provides a web dashboard for visualization. The system includes automated alerting capabilities with state-change detection.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Server-Side Setup](#server-side-setup)
- [Client-Side Setup](#client-side-setup)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [API Documentation](#api-documentation)

---

## 🎯 Overview

This monitoring system consists of three main components:

1. **Monitoring Agent** (`agent.py`) - Runs on client machines to collect system metrics
2. **Flask API Server** (`app_new.py`) - Central server that receives, validates, and stores metrics
3. **Web Dashboard** - Real-time visualization of host metrics and alerts

The system monitors:
- CPU usage percentage
- Memory usage (used/total/percentage)
- Disk usage (used/total/percentage)
- Host online/offline status
- Network information (internal IP, kernel details)

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Client Hosts   │
│                 │
│  agent.py       │───HTTP POST───┐
│  (collects      │   /report      │
│   metrics)      │                │
└─────────────────┘                │
                                    ▼
┌─────────────────────────────────────────────┐
│         Flask API Server (app_new.py)       │
│                                             │
│  • Receives metrics                        │
│  • Validates & authenticates               │
│  • Stores in MySQL                         │
│  • Serves web dashboard                     │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         MySQL Database                      │
│                                             │
│  • hosts (server registry)                 │
│  • incoming_data (time-series metrics)      │
│  • alerts (alert instances)                 │
│  • alert_types (alert definitions)          │
│  • host_alert_checks (per-host config)      │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│   Alert Checker Daemon (in app_new.py)      │
│                                             │
│  • Runs as background thread                │
│  • Checks thresholds periodically           │
│  • State-change detection                   │
│  • Creates/resolves alerts                  │
└─────────────────────────────────────────────┘
```

### Data Flow

1. **Agent** collects system metrics (CPU, memory, disk)
2. **Agent** sends HTTP POST request to Flask API with Bearer token authentication
3. **Flask API** validates the request and authenticates using host_key
4. **Flask API** stores metrics in MySQL `incoming_data` table
5. **Web Dashboard** (requires login) queries database and displays real-time metrics
6. **Alert Checker Daemon** runs as a background thread to check thresholds and trigger alerts automatically

---

## ✨ Features

- ✅ **REST API Architecture** - Clean separation of concerns
- ✅ **Secure Authentication** - Unique host keys for API access, username/password for dashboard
- ✅ **Login System** - User authentication for web dashboard access
- ✅ **Time-Series Data Storage** - Efficient MySQL schema for metrics
- ✅ **Real-Time Web Dashboard** - Auto-refreshing dashboard with visual metrics
- ✅ **Automated Alerting** - Background daemon thread with state-change detection
- ✅ **Configurable Thresholds** - Per-host alert configuration
- ✅ **Multiple Alert Types** - Disk space, memory usage, CPU usage, host online
- ✅ **Alert Resolution Tracking** - Knows when problems are fixed
- ✅ **Easy Setup** - Automated database setup and user creation scripts
- ✅ **Production-Ready** - Error handling, logging, and validation

---

## 📦 Prerequisites

### Server-Side Requirements

- **Python 3.8+**
- **MySQL 5.7+** or **MariaDB 10.3+**
- **pip** (Python package manager)
- **MySQL client** (for database setup)

### Client-Side Requirements

- **Python 3.8+**
- **pip** (Python package manager)
- **psutil** library (for system metrics)

### Network Requirements

- Network connectivity between client hosts and server
- Server must be accessible on configured port (default: 5005)
- MySQL database must be accessible from server

---

## 📁 Project Structure

```
Data_Monitoring_tool/
│
├── README.md                          # This file
├── requirements.txt                   # Python dependencies (root)
├── config.yaml                        # Server configuration (root)
│
├── scripts/                           # Main application code
│   ├── app_new.py                    # Flask API server (MAIN SERVER)
│   ├── agent.py                      # Monitoring agent (CLIENT)
│   ├── config.yaml                   # Server configuration
│   ├── requirements.txt              # Python dependencies
│   ├── setup_database.py             # Database setup script
│   ├── setup_user.py                 # User creation script
│   │
│   ├── templates/                     # Flask HTML templates
│   │   ├── base.html                 # Base template
│   │   ├── login.html                # Login page
│   │   ├── dashboard.html            # Main dashboard
│   │   ├── alerts.html               # Alerts page
│   │   └── host_details.html         # Host detail page
│   │
│   ├── db_fixed.sql                  # Database schema
│   ├── agent_config.json             # Agent configuration template
│   ├── agent_config.json.template    # Agent config template
│   │
│   ├── demo/                         # Demo and testing scripts
│   │   ├── test_monitoring.py        # Test data generator
│   │   ├── demo_alerts.py            # Alert demonstration script
│   │   ├── demo_alerts.py            # Alert demo script
│   │   ├── setup_test_hosts.sql      # Test host setup
│   │   ├── setup_alert_associations.sql  # Alert config setup
│   │   └── templates/                # (duplicate templates for demo)
│   │
│   └── diagnostics.py                # Diagnostic tool
│
└── .venv/                            # Python virtual environment (optional)
```

---

## 🖥️ Server-Side Setup

The server runs the Flask API that receives metrics from agents and serves the web dashboard.

### Step 1: Install Python Dependencies

**Option A: Automated Setup (Recommended)**

```bash
cd scripts

# On Linux/Mac:
chmod +x setup_server.sh
./setup_server.sh

# On Windows:
setup_server.bat
```

**Option B: Manual Setup**

```bash
# Navigate to project root
cd Data_Monitoring_tool

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Required packages:**
- `flask==3.0.0` - Web framework
- `pymysql==1.1.0` - MySQL database connector
- `pydantic==2.5.0` - Data validation
- `pyyaml==6.0.1` - Configuration file parsing
- `werkzeug==3.0.1` - WSGI utilities

### Step 2: Configure Server

Edit `scripts/config.yaml` (or create from template):

```yaml
database:
  host: "mysql.clarksonmsda.org"      # Your MySQL host
  port: 3306                           # MySQL port
  user: "your_username"                # Database username
  password: "your_password"            # Database password
  name: "your_database"                # Database name
  charset: "utf8mb4"

auth:
  header: "Authorization"              # HTTP header for auth
  prefix: "Bearer "                    # Token prefix

flask:
  host: "0.0.0.0"                      # Listen on all interfaces
  port: 5000                           # Server port
  debug: true                          # Debug mode (set false in production)
```

### Step 3: Set Up Database

See [Database Setup](#database-setup) section below.

### Step 4: Verify Setup

Run the diagnostic tool:

```bash
cd scripts
python diagnostics.py
```

This will check:
- Python packages installation
- Configuration files
- Database connectivity
- Network connectivity

### Step 5: Start the Server

```bash
cd scripts
python app_new.py
```

You should see output like:
```
Starting Flask server on 0.0.0.0:5005

Server will be accessible at:
  http://localhost:5005
  http://127.0.0.1:5005
  http://<your-ip>:5005
```

### Step 6: Access the Dashboard

Open your browser and navigate to:
- `http://localhost:5005` or
- `http://<server-ip>:5005`

You should see the monitoring dashboard.

---

## 💻 Client-Side Setup

The client runs the monitoring agent that collects system metrics and sends them to the server.

### Step 1: Install Python Dependencies

**Option A: Automated Setup (Recommended)**

```bash
cd scripts

# On Linux/Mac:
chmod +x setup_client.sh
./setup_client.sh

# On Windows:
setup_client.bat
```

**Option B: Manual Setup**

```bash
# On the client machine, navigate to project directory
cd Data_Monitoring_tool

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Required packages:**
- `requests==2.31.0` - HTTP client
- `psutil==5.9.6` - System metrics collection

### Step 2: Configure Agent

The agent needs to know:
1. **API URL** - Where to send metrics
2. **Host Key** - Unique authentication key for this host

#### Option A: Automatic Configuration (First Run)

Run the agent once - it will create a default config file:

```bash
cd scripts
python agent.py
```

This creates `agent_config.json` with default values. **You must edit this file!**

#### Option B: Manual Configuration

Copy the template and edit it:

```bash
cd scripts
cp agent_config.json.template agent_config.json
```

Edit `agent_config.json`:

```json
{
  "api_url": "http://192.168.1.35:5005/report",
  "host_key": "your-unique-host-key-here",
  "report_interval_seconds": 60
}
```

**Important:**
- `api_url` - Must match your server's IP address and port
- `host_key` - Must match a key in the database `hosts` table (see Database Setup)
- `report_interval_seconds` - How often to send metrics (in seconds)

### Step 3: Register Host in Database

Before the agent can send data, the host must be registered in the database.

**On the server machine**, connect to MySQL and add your host:

```sql
INSERT INTO hosts (host_name, host_key, os_name, os_version, is_active, last_seen) 
VALUES ('my-server-01', 'your-unique-host-key-here', 'Linux', '22.04', 1, NOW());
```

**Important:** The `host_key` must match the key in `agent_config.json`!

### Step 4: Test the Agent

Run the agent manually to test:

```bash
cd scripts
python agent.py
```

You should see output like:
```
============================================================
Monitoring Agent Starting
============================================================
API URL: http://192.168.1.35:5005/report
Host Key: your-key... (masked)
Config File: scripts/agent_config.json

============================================================

Timestamp: 2024-01-15T10:30:00
Hostname: my-server-01
Internal IP: 192.168.1.100
CPU: 15.5%
Memory: 4096/16384 MB (25.0%)
Disk: 125.5/500.0 GB (25.1%)
============================================================

Sending to: http://192.168.1.35:5005/report
✓ Success! Data ID: 12345

✓ Agent run completed successfully
```

### Step 5: Run Agent Automatically

#### Option A: Cron Job (Linux/Mac)

Edit crontab:
```bash
crontab -e
```

Add line to run every minute:
```
* * * * * /usr/bin/python3 /path/to/Data_Monitoring_tool/scripts/agent.py >> /var/log/monitoring_agent.log 2>&1
```

#### Option B: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: "Daily" or "When computer starts"
4. Set action: "Start a program"
5. Program: `python`
6. Arguments: `C:\path\to\Data_Monitoring_tool\scripts\agent.py`
7. Start in: `C:\path\to\Data_Monitoring_tool\scripts`

#### Option C: Systemd Service (Linux)

Create `/etc/systemd/system/monitoring-agent.service`:

```ini
[Unit]
Description=Monitoring Agent
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/Data_Monitoring_tool/scripts
ExecStart=/usr/bin/python3 /path/to/Data_Monitoring_tool/scripts/agent.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable monitoring-agent
sudo systemctl start monitoring-agent
```

---

## 🗄️ Database Setup

### Step 1: Create Database

Connect to MySQL and create the database:

```sql
CREATE DATABASE your_database_name CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 2: Run Database Setup

**Option 1: Using Python Setup Script (Recommended)**

The `setup_database.py` script provides the easiest way to set up the database:

```bash
cd scripts
python setup_database.py
```

This automatically:
- Creates all required tables (hosts, incoming_data, alert_types, alerts, host_alert_checks, users)
- Inserts default alert types if they don't exist
- Provides a summary of what was created

**Option 2: Using SQL Script**

Alternatively, you can use the SQL script directly:

```bash
cd scripts
mysql -h your_mysql_host -u your_username -p your_database_name < db_fixed.sql
```

This creates all required tables:
- `hosts` - Server registry (includes one test host: `test-host` with key `test-key-123`)
- `incoming_data` - Time-series metrics
- `alert_types` - Alert check definitions (includes default alert types)
- `alerts` - Alert instances
- `host_alert_checks` - Per-host alert configuration

**Note:** The `users` table is created automatically by `setup_database.py`. If using SQL script only, you'll need to create it separately or run `setup_database.py` afterwards.

### Step 3: Create User Account

Create your first login account for the dashboard:

```bash
cd scripts
python setup_user.py admin your_password
```

Replace `admin` and `your_password` with your desired username and password.

### Step 4: Add Additional Test Hosts (Optional)

If you want to add more test hosts for demonstration purposes:

```bash
mysql -h your_mysql_host -u your_username -p your_database_name < scripts/demo/setup_test_hosts.sql
```

This adds additional test hosts with different scenarios (high CPU, high memory, high disk).

### Step 5: Configure Alert Associations (Optional)

To set up alert associations for the test hosts:

```bash
mysql -h your_mysql_host -u your_username -p your_database_name < scripts/demo/setup_alert_associations.sql
```

This configures which alerts are enabled for which hosts with custom thresholds.

### Step 6: Verify Database

Connect to MySQL and verify:

```sql
USE your_database_name;

-- Check tables
SHOW TABLES;

-- Check hosts
SELECT * FROM hosts;

-- Check alert types
SELECT * FROM alert_types;
```

---

## ⚙️ Configuration

### Server Configuration (`scripts/config.yaml`)

```yaml
database:
  host: "mysql.clarksonmsda.org"      # MySQL server hostname
  port: 3306                           # MySQL port
  user: "your_username"                 # Database username
  password: "your_password"             # Database password
  name: "your_database"                 # Database name
  charset: "utf8mb4"                   # Character set

auth:
  header: "Authorization"              # HTTP header name for authentication
  prefix: "Bearer "                     # Token prefix (include trailing space)

flask:
  host: "0.0.0.0"                      # Bind to all interfaces (use 127.0.0.1 for localhost only)
  port: 5005                            # Server port (default: 5005)
  debug: true                          # Debug mode (set false in production)

alerts:
  check_interval_seconds: 60           # How often to check for alerts (in seconds)
```

### Agent Configuration (`scripts/agent_config.json`)

```json
{
  "api_url": "http://192.168.1.35:5005/report",
  "host_key": "unique-host-key-123",
  "report_interval_seconds": 60
}
```

**Configuration Fields:**
- `api_url` - Full URL to the `/report` endpoint
- `host_key` - Unique key that matches database `hosts.host_key`
- `report_interval_seconds` - How often to send metrics (for cron/scheduler)

---

## 🚀 Running the System

### Start the Server

```bash
cd scripts
python app_new.py
```

The server will:
- Load configuration from `config.yaml`
- Connect to MySQL database
- Start Flask web server
- Display accessible URLs

### Run the Agent

**Manual (one-time):**
```bash
cd scripts
python agent.py
```

**Automated (cron/scheduler):**
See [Client-Side Setup - Step 5](#step-5-run-agent-automatically)

### Alert Checker (Automatic)

The alert checker is now integrated into the Flask application and runs automatically as a background thread. When you start `app_new.py`, the alert checker daemon starts automatically.

The check interval can be configured in `config.yaml`:

```yaml
alerts:
  check_interval_seconds: 60  # How often to check for alerts (in seconds)
```

**No separate script or cron job needed!** The alert checking runs continuously in the background.

---

## 📖 Usage

### Web Dashboard

Access the dashboard at `http://<server-ip>:5005` (or your configured port)

**Login Required:**
- You'll be redirected to the login page
- Use credentials created with `setup_user.py`

**Pages:**
- **Login** (`/login`) - User authentication page
- **Dashboard** (`/` or `/dashboard`) - Overview of all hosts with metrics
- **Alerts** (`/alerts`) - List of all alerts (open, acknowledged, resolved)
- **Host Details** (`/host/<id>`) - Detailed view of a specific host
- **Add Host** (`/add-host`) - Add a new host to monitor

**Features:**
- User authentication with session management
- Auto-refreshes every 30 seconds
- Color-coded metrics (green/yellow/red)
- Status indicators (online/warning/offline)
- Alert badges on host cards
- Logout functionality

### API Endpoints

#### POST `/report`

Send metrics from agent to server.

**Headers:**
```
Authorization: Bearer <host_key>
Content-Type: application/json
```

**Body:**
```json
{
  "host_key": "unique-host-key",
  "collected_at": "2024-01-15T10:30:00",
  "int_ip": "192.168.1.100",
  "kernel_name": "Linux",
  "kernel_version": "5.15.0",
  "cpu_pct": 15.5,
  "mem_used_mb": 4096,
  "mem_total_mb": 16384,
  "mem_pct": 25.0,
  "disk_used_gb": 125.5,
  "disk_total_gb": 500.0,
  "disk_pct": 25.1
}
```

**Response:**
```json
{
  "ok": true,
  "data_id": 12345
}
```

#### GET `/health`

Health check endpoint.

**Response:**
```json
{
  "ok": true
}
```

### Adding a New Host

1. **Generate a unique host key:**
   ```python
   import secrets
   host_key = secrets.token_urlsafe(32)
   print(host_key)
   ```

2. **Add to database:**
   ```sql
   INSERT INTO hosts (host_name, host_key, os_name, os_version, is_active, last_seen) 
   VALUES ('new-server', 'generated-key-here', 'Linux', '22.04', 1, NOW());
   ```

3. **Configure agent:**
   Edit `agent_config.json` on the client machine with the new `host_key`

4. **Run agent:**
   The agent will start sending metrics automatically

---

## 🔧 Troubleshooting

### Server Issues

**Problem: Flask server won't start**

**Solutions:**
- Check if port 5000 is already in use: `netstat -an | grep 5000`
- Verify `config.yaml` exists and is valid YAML
- Check Python dependencies: `pip list`
- Check database connectivity: `python diagnostics.py`

**Problem: Database connection error**

**Solutions:**
- Verify MySQL server is running
- Check database credentials in `config.yaml`
- Test connection: `mysql -h host -u user -p`
- Verify database exists: `SHOW DATABASES;`
- Check firewall rules

**Problem: Templates not found**

**Solutions:**
- Ensure `templates/` directory exists in `scripts/`
- Verify templates are HTML files (not markdown)
- Check Flask can find templates: run from `scripts/` directory

### Agent Issues

**Problem: Agent can't connect to server**

**Solutions:**
- Verify `api_url` in `agent_config.json` is correct
- Check server is running: `curl http://server-ip:5005/health`
- Check network connectivity: `ping server-ip`
- Check firewall rules on both client and server

**Problem: Authentication failed (403 error)**

**Solutions:**
- Verify `host_key` in `agent_config.json` matches database
- Check host exists: `SELECT * FROM hosts WHERE host_key='your-key';`
- Verify host is active: `SELECT * FROM hosts WHERE host_key='your-key' AND is_active=1;`

**Problem: No metrics collected**

**Solutions:**
- Check `psutil` is installed: `pip install psutil`
- Run agent with verbose output to see errors
- Check file permissions (agent needs to read system info)

### Database Issues

**Problem: Tables don't exist**

**Solutions:**
- Run schema script: `mysql < scripts/db_fixed.sql`
- Check database name in `config.yaml`
- Verify user has CREATE TABLE permissions

**Problem: Data not appearing in dashboard**

**Solutions:**
- Check `incoming_data` table: `SELECT * FROM incoming_data ORDER BY collected_at DESC LIMIT 10;`
- Verify host_id matches: `SELECT * FROM hosts;`
- Check Flask server logs for errors
- Make sure you're logged in (dashboard requires authentication)

**Problem: Cannot access dashboard / login page not working**

**Solutions:**
- Create a user account: `python setup_user.py admin password`
- Verify users table exists: `SELECT * FROM users;`
- Check that setup_database.py was run successfully

### General Issues

**Use the diagnostic tool:**
```bash
cd scripts
python diagnostics.py
```

This will check:
- Package installation
- Configuration files
- Database connectivity
- API connectivity
- System metrics collection

---

## 📚 API Documentation

### Authentication

**API Endpoints** (for monitoring agents):
All API requests use Bearer token authentication via the `Authorization` header:

```
Authorization: Bearer <host_key>
```

The `host_key` must exist in the `hosts` table and the host must be active (`is_active=1`).

**Web Dashboard**:
The web dashboard requires user login. Create user accounts using `setup_user.py`. All dashboard routes are protected with session-based authentication.

### Endpoints

#### `POST /report`

Receives metrics from monitoring agents.

**Request:**
- Method: `POST`
- Headers: `Authorization: Bearer <host_key>`, `Content-Type: application/json`
- Body: JSON with metrics (see Usage section)

**Response:**
- `200 OK`: `{"ok": true, "data_id": <id>}`
- `400 Bad Request`: Invalid JSON or validation error
- `401 Unauthorized`: Missing or invalid host_key
- `403 Forbidden`: Host not found or inactive
- `500 Internal Server Error`: Server error

#### `GET /health`

Health check endpoint.

**Response:**
- `200 OK`: `{"ok": true}`

#### `GET /` or `GET /dashboard`

Web dashboard (HTML).

#### `GET /alerts`

Alerts page (HTML).

#### `GET /host/<host_id>`

Host details page (HTML).

---

## 🔐 Security Considerations

### Production Deployment

1. **Change default host keys** - Never use `test-key-123` in production
2. **Use HTTPS** - Set up SSL/TLS for the Flask server
3. **Disable debug mode** - Set `debug: false` in `config.yaml`
4. **Secure database** - Use strong passwords and limit access
5. **Firewall rules** - Only allow necessary ports
6. **Regular updates** - Keep Python packages updated

### Host Key Generation

Generate secure host keys:

```python
import secrets
host_key = secrets.token_urlsafe(32)
print(host_key)
```

---

## 📝 License

This project is for educational/demonstration purposes.

---

## 🤝 Contributing

This is a project for academic demonstration. For questions or issues, contact the project maintainer.

---

## 📞 Support

For issues or questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Run `python diagnostics.py` for system checks
3. Review server logs for error messages
4. Check database connectivity and permissions

---

**Last Updated:** 2024-01-15

