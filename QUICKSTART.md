# Quick Start Guide

Get the monitoring system up and running in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] MySQL database accessible
- [ ] Network connectivity between client and server

## Server Setup (5 minutes)

### 1. Run Setup Script

```bash
cd scripts

# Linux/Mac:
chmod +x setup_server.sh
./setup_server.sh

# Windows:
setup_server.bat
```

### 2. Configure Database

Edit `scripts/config.yaml`:

```yaml
database:
  host: "your-mysql-host"
  port: 3306
  user: "your-username"
  password: "your-password"
  name: "your-database"
```

### 3. Create Database Schema

**Option 1: Using Python Setup Script (Recommended)**
```bash
cd scripts
python setup_database.py
```

This automatically creates all required tables, including the users table, and sets up default alert types.

**Option 2: Using SQL Script**
```bash
mysql -h your-mysql-host -u your-username -p your-database < scripts/db_fixed.sql
```

This creates all tables, adds default alert types, and includes one test host (`test-host` with key `test-key-123`).

### 4. Create Initial User Account

```bash
cd scripts
python setup_user.py admin your_password
```

This creates your first login account for the dashboard.

### 5. Start Server

```bash
cd scripts
python app_new.py
```

Server will be available at `http://localhost:5005` (or the port configured in config.yaml)

## Client Setup (3 minutes)

### 1. Run Setup Script

```bash
cd scripts

# Linux/Mac:
chmod +x setup_client.sh
./setup_client.sh

# Windows:
setup_client.bat
```

### 2. Configure Agent

Edit `scripts/agent_config.json`:

```json
{
  "api_url": "http://YOUR-SERVER-IP:5000/report",
  "host_key": "your-unique-key-here",
  "report_interval_seconds": 60
}
```

### 3. Register Host in Database

On the server, run:

```sql
INSERT INTO hosts (host_name, host_key, os_name, os_version, is_active, last_seen) 
VALUES ('my-server', 'your-unique-key-here', 'Linux', '22.04', 1, NOW());
```

### 4. Test Agent

```bash
cd scripts
python agent.py
```

You should see: `✓ Success! Data ID: <number>`

## Verify Everything Works

1. **Check Dashboard**: Open `http://YOUR-SERVER-IP:5005` (or your configured port) in browser
   - You'll be redirected to the login page
   - Log in with the credentials you created using `setup_user.py`
2. **Check Database**: 
   ```sql
   SELECT * FROM incoming_data ORDER BY collected_at DESC LIMIT 5;
   ```
3. **Check Agent**: Run `python agent.py` and verify success message
4. **Check Alerts**: The alert checker daemon runs automatically in the background when the Flask server starts

## Next Steps

- Set up automatic agent runs (cron/Task Scheduler)
- Configure alerts (see `scripts/demo/setup_alert_associations.sql`)
- The alert checker runs automatically as a background thread when you start the Flask server
- Adjust alert check interval in `config.yaml` if needed

## Troubleshooting

If something doesn't work:

1. Run diagnostics: `python scripts/diagnostics.py`
2. Check server logs for errors
3. Verify database connection
4. Check network connectivity

For detailed troubleshooting, see README.md

