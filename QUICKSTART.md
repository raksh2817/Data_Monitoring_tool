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

```bash
mysql -h your-mysql-host -u your-username -p your-database < scripts/db_fixed.sql
```

### 4. Start Server

```bash
cd scripts
python app_new.py
```

Server will be available at `http://localhost:5000`

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

1. **Check Dashboard**: Open `http://YOUR-SERVER-IP:5000` in browser
2. **Check Database**: 
   ```sql
   SELECT * FROM incoming_data ORDER BY collected_at DESC LIMIT 5;
   ```
3. **Check Agent**: Run `python agent.py` and verify success message

## Next Steps

- Set up automatic agent runs (cron/Task Scheduler)
- Configure alerts (see `scripts/demo/setup_alert_associations.sql`)
- Set up alert checker (see README.md)

## Troubleshooting

If something doesn't work:

1. Run diagnostics: `python scripts/diagnostics.py`
2. Check server logs for errors
3. Verify database connection
4. Check network connectivity

For detailed troubleshooting, see README.md

