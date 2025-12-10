# Project Structure

This document describes the organization of the Data Monitoring Tool project.

## Directory Layout

```
Data_Monitoring_tool/
│
├── README.md                          # Main documentation (comprehensive)
├── QUICKSTART.md                      # Quick start guide (5-minute setup)
├── PROJECT_STRUCTURE.md               # This file
├── requirements.txt                   # Root-level dependencies (all packages)
│
├── scripts/                           # Main application code
│   │
│   ├── app_new.py                     # ⭐ Flask API Server (MAIN)
│   ├── agent.py                       # ⭐ Monitoring Agent (CLIENT)
│   │
│   ├── config.yaml                    # Server configuration
│   ├── requirements.txt               # Server dependencies
│   │
│   ├── templates/                     # Flask HTML templates
│   │   ├── base.html                  # Base template with navigation
│   │   ├── login.html                 # Login page
│   │   ├── dashboard.html             # Main dashboard page
│   │   ├── alerts.html                # Alerts listing page
│   │   ├── host_details.html          # Individual host details
│   │   └── add_host.html              # Add host page
│   │
│   ├── agent_config.json              # Agent configuration (per client)
│   ├── agent_config.json.template     # Agent config template
│   │
│   ├── db_fixed.sql                   # Database schema
│   ├── setup_database.py              # Database setup script
│   ├── setup_user.py                  # User creation script
│   │
│   ├── setup_server.sh                # Server setup script (Linux/Mac)
│   ├── setup_server.bat               # Server setup script (Windows)
│   ├── setup_client.sh                # Client setup script (Linux/Mac)
│   ├── setup_client.bat               # Client setup script (Windows)
│   │
│   ├── diagnostics.py                 # System diagnostic tool
│   │
│   └── demo/                          # Demo and testing scripts
│       ├── test_monitoring.py         # Test data generator
│       ├── demo_alerts.py             # Alert demonstration
│       ├── verify_demo.py             # Verification script
│       ├── setup_test_hosts.sql       # Test host setup
│       ├── setup_alert_associations.sql  # Alert configuration
│       ├── DEMO_SCRIPT.md              # Demo instructions
│       ├── COMPLETE_DEMO_WITH_ALERTS.md  # Complete demo guide
│       └── FLOWCHART_FOR_SCREENSHOT.txt  # Flowchart documentation
│
└── .venv/                             # Python virtual environment (gitignored)
```

## Key Files

### Production Files (Core System)

| File | Purpose | Location |
|------|---------|----------|
| `app_new.py` | Flask API server - receives metrics, serves dashboard, runs alert daemon | `scripts/` |
| `agent.py` | Monitoring agent - collects and sends metrics | `scripts/` |
| `config.yaml` | Server configuration (database, auth, Flask, alerts) | `scripts/` |
| `agent_config.json` | Agent configuration (API URL, host key) | `scripts/` |
| `db_fixed.sql` | Database schema | `scripts/` |
| `setup_database.py` | Automated database setup script | `scripts/` |
| `setup_user.py` | User account creation script | `scripts/` |
| `templates/*.html` | Web dashboard templates (includes login.html) | `scripts/templates/` |

### Setup & Documentation

| File | Purpose |
|------|---------|
| `README.md` | Comprehensive documentation |
| `QUICKSTART.md` | Quick 5-minute setup guide |
| `IMPLEMENTATION_SUMMARY.md` | Summary of recent implementation changes |
| `setup_server.sh/.bat` | Automated server setup |
| `setup_client.sh/.bat` | Automated client setup |
| `setup_database.py` | Database initialization script |
| `setup_user.py` | User account creation script |
| `diagnostics.py` | System diagnostic tool |

### Demo & Testing

| File | Purpose | Location |
|------|---------|----------|
| `test_monitoring.py` | Simulates multiple hosts sending data | `scripts/demo/` |
| `demo_alerts.py` | Demonstrates alert system | `scripts/demo/` |

**Note**: Alert checking is now integrated into `app_new.py` as a background daemon thread and runs automatically when the Flask server starts.

## File Organization Principles

1. **Separation of Concerns**
   - Production code in `scripts/`
   - Demo/testing code in `scripts/demo/`
   - Templates in `scripts/templates/`

2. **Platform Support**
   - Shell scripts (`.sh`) for Linux/Mac
   - Batch scripts (`.bat`) for Windows
   - Python code is cross-platform

3. **Configuration**
   - Server config: `scripts/config.yaml`
   - Client config: `scripts/agent_config.json`
   - Templates provided for easy setup

4. **Documentation**
   - `README.md` - Full documentation
   - `QUICKSTART.md` - Fast setup
   - `PROJECT_STRUCTURE.md` - This file

## Where to Start

1. **New User**: Read `QUICKSTART.md`
2. **Detailed Setup**: Read `README.md`
3. **Understanding Structure**: Read this file
4. **Troubleshooting**: See `README.md` Troubleshooting section

## Important Notes

- **Templates**: Must be in `scripts/templates/` for Flask to find them
- **Config Files**: Server uses `scripts/config.yaml`, agent uses `scripts/agent_config.json`
- **Database**: Run `setup_database.py` to create all tables (recommended) or use `db_fixed.sql`
- **User Accounts**: Run `setup_user.py` to create login accounts for the dashboard
- **Alert System**: Runs automatically as a background thread in `app_new.py` (no separate script needed)
- **Virtual Environment**: Recommended but optional (`.venv/` directory)

## Adding New Features

- **New API endpoints**: Add to `app_new.py`
- **New alert types**: Add functions to `app_new.py` (alert checking is integrated into the main application)
- **New dashboard pages**: Add templates to `scripts/templates/` and routes to `app_new.py` (protect with `@login_required`)
- **New metrics**: Modify `agent.py` to collect, update `app_new.py` to store

