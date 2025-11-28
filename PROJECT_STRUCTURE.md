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
│   │   ├── dashboard.html             # Main dashboard page
│   │   ├── alerts.html                # Alerts listing page
│   │   └── host_details.html          # Individual host details
│   │
│   ├── agent_config.json              # Agent configuration (per client)
│   ├── agent_config.json.template     # Agent config template
│   │
│   ├── db_fixed.sql                   # Database schema
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
│       ├── check_alerts.py            # Alert checker script
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
| `app_new.py` | Flask API server - receives metrics, serves dashboard | `scripts/` |
| `agent.py` | Monitoring agent - collects and sends metrics | `scripts/` |
| `config.yaml` | Server configuration (database, auth, Flask) | `scripts/` |
| `agent_config.json` | Agent configuration (API URL, host key) | `scripts/` |
| `db_fixed.sql` | Database schema | `scripts/` |
| `templates/*.html` | Web dashboard templates | `scripts/templates/` |

### Setup & Documentation

| File | Purpose |
|------|---------|
| `README.md` | Comprehensive documentation |
| `QUICKSTART.md` | Quick 5-minute setup guide |
| `setup_server.sh/.bat` | Automated server setup |
| `setup_client.sh/.bat` | Automated client setup |
| `diagnostics.py` | System diagnostic tool |

### Demo & Testing

| File | Purpose | Location |
|------|---------|----------|
| `test_monitoring.py` | Simulates multiple hosts sending data | `scripts/demo/` |
| `check_alerts.py` | Alert checking script | `scripts/demo/` |
| `demo_alerts.py` | Demonstrates alert system | `scripts/demo/` |

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
- **Database**: Schema in `scripts/db_fixed.sql` must be run first
- **Virtual Environment**: Recommended but optional (`.venv/` directory)

## Adding New Features

- **New API endpoints**: Add to `app_new.py`
- **New alert types**: Add functions to `scripts/demo/check_alerts.py`
- **New dashboard pages**: Add templates to `scripts/templates/` and routes to `app_new.py`
- **New metrics**: Modify `agent.py` to collect, update `app_new.py` to store

