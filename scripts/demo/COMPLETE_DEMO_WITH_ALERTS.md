# COMPLETE DEMO SCRIPT - WITH ALERT SYSTEM
# For November 26 Meeting

## Setup (Do Before Meeting)

### 1. Database Setup
```bash
# Create tables
mysql -h mysql.clarksonmsda.org -u srinatr -p srinatr_monitor < db_fixed.sql

# Add test hosts
mysql -h mysql.clarksonmsda.org -u srinatr -p srinatr_monitor < setup_test_hosts.sql

# Configure alert associations
mysql -h mysql.clarksonmsda.org -u srinatr -p srinatr_monitor < setup_alert_associations.sql
```

### 2. Start Flask Server
```bash
python app.py
```

Keep this terminal open!

---

## DEMO FLOW (20 minutes)

### Part 1: System Overview (2 minutes)

**Say:** "I've built a complete data monitoring system with automated alerting."

**Components:**
1. **Monitoring Agents** - Collect CPU, memory, disk metrics
2. **REST API** - Flask server for data ingestion
3. **Database** - MySQL for time-series storage
4. **Alert System** - Automated threshold monitoring

---

### Part 2: Database Schema (3 minutes)

**Show:** Tables and relationships

```sql
SHOW TABLES;
```

**Explain each table:**

1. **hosts** - Server registry
   - Unique host_key for authentication
   - Tracks last_seen timestamp

2. **incoming_data** - Metrics time-series
   - CPU, memory, disk usage
   - Supports pipeline monitoring (files, datasets)

3. **alert_types** - Alert definitions
   - Python function for each check
   - Configurable parameters (thresholds)

4. **host_alert_checks** - Per-host alert configuration
   - Different thresholds per host
   - Enable/disable specific checks

5. **alerts** - Alert history
   - State changes (open → resolved)
   - Prevents duplicate notifications

---

### Part 3: Data Collection Demo (4 minutes)

**Terminal: Run test data generator**
```bash
python test_monitoring.py
```

**Show:**
- 4 servers reporting metrics
- Different usage patterns
- Real-time data flow

**Explain:** "Using test scripts as suggested. In production, these would be real agents on Linux servers."

**Verify data:**
```bash
mysql -h mysql.clarksonmsda.org -u srinatr -p -e "
USE srinatr_monitor;
SELECT 
    h.host_name,
    i.collected_at,
    i.cpu_pct,
    i.mem_pct,
    i.disk_pct
FROM incoming_data i
JOIN hosts h ON i.host_id = h.host_id
ORDER BY i.collected_at DESC
LIMIT 5;
"
```

---

### Part 4: Alert System - LIVE DEMO (8 minutes)

This is the key differentiator!

#### 4A: Show Alert Configuration (2 min)

**Query alert types:**
```sql
SELECT check_name, check_key, function_name, params_json 
FROM alert_types;
```

**Query alert associations:**
```sql
SELECT 
    h.host_name,
    at.check_name,
    hac.params_json as threshold
FROM host_alert_checks hac
JOIN hosts h ON hac.host_id = h.host_id
JOIN alert_types at ON hac.check_id = at.check_id
WHERE hac.enabled = 1
ORDER BY h.host_name;
```

**Explain:** "Each host has configurable thresholds. For example, the database server has stricter memory limits."

#### 4B: Trigger Alerts Live (3 min)

**Run the alert demo:**
```bash
python demo_alerts.py
```

This will:
1. Send normal metrics
2. Run alert checker → All OK
3. Send critical metrics (high disk/memory)
4. Run alert checker → **Alerts triggered!** 🚨
5. Send normal metrics
6. Run alert checker → **Alerts resolved!** ✅

**Between each step, run:**
```bash
python check_alerts.py
```

**Show the output** - point out:
- State change detection
- Only alerts on transitions (not every check)
- Alert messages show exactly what's wrong

#### 4C: View Alert History (3 min)

**Query alerts table:**
```sql
SELECT 
    a.alert_id,
    h.host_name,
    at.check_name,
    a.severity,
    a.status,
    a.triggered_at,
    LEFT(a.message, 100) as message
FROM alerts a
JOIN hosts h ON a.host_id = h.host_id
JOIN alert_types at ON a.check_id = at.check_id
ORDER BY a.triggered_at DESC
LIMIT 10;
```

**Point out:**
- Alert #X was triggered when disk hit 92%
- Alert #Y was resolved when it dropped to 45%
- Status tracking (open → resolved)
- Complete audit trail

---

### Part 5: How Alert System Works (3 minutes)

**Explain the algorithm:**

```python
# Simplified pseudocode
for each host:
    for each alert_check configured:
        current_state = run_check_function(host, params)
        previous_state = get_last_alert_status(host, check)
        
        if current_state == ALERT and previous_state != ALERT:
            create_alert(host, check, message)  # State changed!
        
        elif current_state == OK and previous_state == ALERT:
            resolve_alert(host, check, message)  # Recovered!
        
        # else: no state change, do nothing
```

**Key features:**
1. **State-change detection** - Only alerts on transitions
2. **No spam** - Won't create duplicate alerts
3. **Resolution tracking** - Knows when problems are fixed
4. **Configurable thresholds** - Per-host customization
5. **Audit trail** - Complete history in database

---

### Part 6: Production Deployment (2 minutes)

**Explain how this would run in production:**

1. **Agents** run on each monitored server
   ```bash
   # Cron job - every minute
   * * * * * /usr/bin/python3 /opt/monitoring/agent.py
   ```

2. **Alert checker** runs periodically
   ```bash
   # Cron job - every 2 minutes
   */2 * * * * /usr/bin/python3 /opt/monitoring/check_alerts.py
   ```

3. **Flask API** runs as systemd service
   ```bash
   sudo systemctl start monitoring-api
   ```

4. **Future enhancements:**
   - Email notifications
   - Slack integration
   - Web dashboard
   - SMS alerts (Twilio)
   - Custom alert rules

---

## Files to Have Open

1. `db_fixed.sql` - Show schema
2. `check_alerts.py` - Show alert logic
3. `agent.py` - Show real agent code
4. `test_monitoring.py` - For demo
5. `demo_alerts.py` - For alert demo
6. MySQL client - For queries

---

## Key Talking Points

### What Makes This System Professional:

1. ✅ **Proper Architecture**
   - REST API (not direct DB access)
   - Separation of concerns
   - Stateless agents

2. ✅ **Security**
   - Authentication via unique keys
   - Per-host authorization
   - Invalid keys rejected

3. ✅ **Scalability**
   - Time-series data model
   - Supports unlimited hosts
   - Efficient queries with indexes

4. ✅ **Alert System**
   - State-change detection (smart!)
   - Configurable thresholds
   - No duplicate notifications
   - Resolution tracking

5. ✅ **Production-Ready**
   - Error handling
   - Logging
   - Configuration files
   - Real code that works

---

## Q&A Preparation

**Q: Why state-change detection instead of threshold checks?**
A: Prevents alert spam. If CPU stays at 95% for an hour, you get ONE alert when it crosses the threshold and ONE when it recovers. Not 30 alerts every 2 minutes.

**Q: How do you prevent alert spam?**
A: Three ways:
1. State-change detection (only alert on transitions)
2. Status tracking in database (open/resolved)
3. Cooldown periods (configurable per alert type)

**Q: Can you add new alert types?**
A: Yes! Just:
1. Write a Python function that returns True/False
2. Add to alert_types table
3. Associate with hosts
The framework is completely extensible.

**Q: What about false positives?**
A: Thresholds are configurable per host. We can:
- Adjust sensitivity (80% vs 90%)
- Require sustained condition (average over 5 minutes)
- Implement "flap detection" (ignore rapidly changing states)

**Q: How would notifications work?**
A: Add to check_alerts.py:
```python
if alert_triggered:
    create_alert(...)
    send_email(alert_message)
    post_to_slack(alert_message)
```

**Q: Can this monitor data pipelines?**
A: Yes! The incoming_data table has fields for:
- dataset_name
- partition_key
- files_count
- event timestamps
Same alert framework applies.

---

## Demo Timeline

| Activity | Time | What to Show |
|----------|------|--------------|
| Overview | 2 min | Architecture diagram |
| Database | 3 min | Tables & relationships |
| Data Collection | 4 min | Test script + queries |
| **Alert System** | 8 min | **Live demo!** |
| Architecture | 3 min | How it works |
| Q&A | 5 min | Answer questions |
| **Total** | **25 min** | Buffer included |

---

## Success Criteria

✓ Flask server running
✓ Test data flowing
✓ **Alerts trigger correctly**
✓ **Alerts resolve correctly**
✓ Can query all data
✓ Can explain architecture
✓ Can answer questions

---

## The "Wow" Moment

**When you run `check_alerts.py` and show:**
```
🚨 NEW ALERT #15: Disk Space - Host 'storage-server-04' disk usage critical: 92%
```

**Then later:**
```
✅ RESOLVED: Disk Space - Host 'storage-server-04' disk usage normal: 45%
```

**This shows:**
- System is intelligent (state-aware)
- Not just threshold checking
- Production-quality implementation

---

## Backup Plan

If alert demo has issues:
1. Show previous successful run screenshots
2. Query alerts table to show historical data
3. Walk through code logic
4. Explain the algorithm

You're demonstrating a **complete, working system** with real production-quality features!

**You've got this!** 🚀
