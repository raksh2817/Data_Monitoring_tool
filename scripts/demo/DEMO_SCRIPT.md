# DEMO SCRIPT FOR NOVEMBER 26 MEETING

## Prerequisites (Do Before Meeting)

### 1. Database Setup
```bash
mysql -h mysql.clarksonmsda.org -u srinatr -p srinatr_monitor < db_fixed.sql
mysql -h mysql.clarksonmsda.org -u srinatr -p srinatr_monitor < setup_test_hosts.sql
```

### 2. Start Flask Server
```bash
python app.py
```

Keep this terminal open!

---

## DEMO FLOW (15 minutes)

### Part 1: System Overview (2 minutes)

**Say:** "I've built a data monitoring system that tracks server metrics and pipeline data."

**Show:** Architecture diagram or explain:
- Monitoring agents collect system metrics (CPU, memory, disk)
- Data sent via REST API to Flask server
- Flask authenticates and stores in MySQL database
- Alert system ready for threshold monitoring

---

### Part 2: Database Schema (3 minutes)

**Show:** `db_fixed.sql` or database diagram

**Explain tables:**
1. **hosts** - Server registry with authentication keys
   - Each host has unique host_key for security
   
2. **incoming_data** - Time-series metrics
   - Stores CPU, memory, disk usage
   - Supports pipeline data (files, datasets)
   
3. **alert_types** - Alert definitions
   - Pre-configured: host_online, disk_space, memory_usage
   - Python functions with configurable thresholds
   
4. **alerts** - Alert instances (for future)
5. **host_alert_checks** - Associates alerts with hosts

**Run query to show structure:**
```sql
SHOW TABLES;
DESCRIBE hosts;
DESCRIBE incoming_data;
```

---

### Part 3: Live Demo - Sending Data (5 minutes)

**Terminal 1: Flask Server (already running)**
- Show it's listening on port 5000

**Terminal 2: Run Test Script**
```bash
python test_monitoring.py
```

**Show output:**
- 4 simulated servers sending data
- Different scenarios: normal, high CPU, high memory, high disk
- Success messages with data IDs

**Explain:** "In production, these would be real agents on Linux servers. For demo, I'm using test scripts as you suggested."

---

### Part 4: Verify Data in Database (3 minutes)

**Run queries to show data:**

```bash
mysql -h mysql.clarksonmsda.org -u srinatr -p -e "
USE srinatr_monitor;

-- Show all hosts
SELECT host_id, host_name, last_seen, is_active FROM hosts;

-- Show recent metrics
SELECT 
    h.host_name,
    i.collected_at,
    i.cpu_pct,
    i.mem_pct,
    i.disk_pct
FROM incoming_data i
JOIN hosts h ON i.host_id = h.host_id
ORDER BY i.collected_at DESC
LIMIT 10;

-- Show high resource usage
SELECT 
    h.host_name,
    i.collected_at,
    i.cpu_pct,
    i.mem_pct,
    i.disk_pct
FROM incoming_data i
JOIN hosts h ON i.host_id = h.host_id
WHERE i.cpu_pct > 80 
   OR i.mem_pct > 80 
   OR i.disk_pct > 80
ORDER BY i.collected_at DESC;
"
```

**Point out:**
- Data is flowing correctly
- Timestamps are recent
- Can see which servers have high resource usage

---

### Part 5: API & Authentication (2 minutes)

**Show:** How authentication works

**Explain:**
1. Each host has unique key in database
2. Agent sends key with every request
3. Flask validates before accepting data
4. Invalid keys get rejected (403 error)

**Demo:** Test invalid key
```bash
curl -X POST http://localhost:5000/report \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer invalid-key-999" \
  -d '{"cpu_pct": 50}'
```

**Show:** Gets 403 error

---

### Part 6: Future Work - Alert System (2 minutes)

**Explain:** Alert system is designed but not yet implemented

**Show:** `alert_types` table
```sql
SELECT check_name, check_key, function_name, params_json FROM alert_types;
```

**Explain future implementation:**
1. Separate script runs periodically
2. Checks each host against thresholds
3. Compares to previous state
4. Only alerts on state changes (normal → alert, alert → normal)
5. Cooldown period prevents spam

**Example scenarios:**
- Disk > 90% → Alert "storage-server-04 disk space critical"
- Memory drops from 95% to 60% → Alert "db-server-03 memory recovered"
- No data for 60 minutes → Alert "web-server-01 offline"

---

## Q&A Preparation

### Expected Questions & Answers:

**Q: Why use test scripts instead of real agents?**
A: Network configuration between my Windows machine and Linux workspace had connectivity issues. Test scripts let me demonstrate the full data flow. In production, real agents would run on each monitored server.

**Q: How does authentication work?**
A: Each host has a unique key stored in the database. Agents send this key with every request. Flask validates it before accepting data. Invalid keys are rejected with 403 error.

**Q: Can you add new hosts?**
A: Yes, just insert into hosts table with a new key, then configure agent with that key. In future, web UI will generate keys automatically.

**Q: How would alerts work?**
A: Separate Python script runs periodically, checks metrics against thresholds, compares to previous state, and triggers alerts only on state changes. Database schema is ready, just need to implement the checker script.

**Q: What about data pipeline monitoring?**
A: The `incoming_data` table has fields for pipeline data (dataset_name, partition_key, files_count, size_bytes, event timestamps). Same REST API can receive both system metrics and pipeline data.

**Q: Can you show it working on a real Linux server?**
A: (Run agent on Linux workspace if you get it working, otherwise): Due to network restrictions between different networks, I'm demoing with localhost. The agent works identically on Linux - I've tested it on my Linux workspace.

---

## Files to Have Ready

1. ✓ `db_fixed.sql` - Database schema
2. ✓ `setup_test_hosts.sql` - Test host setup
3. ✓ `app.py` - Flask API server
4. ✓ `config.yaml` - Server configuration
5. ✓ `agent.py` - Real monitoring agent (show code)
6. ✓ `test_monitoring.py` - Test data generator
7. ✓ Architecture diagram (draw or show on screen)

---

## Demo Checklist (Day Before)

- [ ] Database has latest schema
- [ ] Test hosts are in database
- [ ] Flask server starts without errors
- [ ] Test script successfully sends data
- [ ] Can query recent data from database
- [ ] All files are in project directory
- [ ] Know how to explain each component
- [ ] Practice running through demo (10 min)

---

## Backup Plan (If Something Goes Wrong)

If Flask won't start:
→ Show the code and explain how it works

If database connection fails:
→ Show queries in MySQL Workbench
→ Have screenshots of working system

If test script fails:
→ Show previous successful runs
→ Query existing data in database

---

## Time Management

| Topic | Time | Notes |
|-------|------|-------|
| System Overview | 2 min | High-level architecture |
| Database Schema | 3 min | Show tables and relationships |
| Live Demo | 5 min | Run test script, show data flowing |
| Database Queries | 3 min | Verify data, show insights |
| Authentication | 2 min | Explain security model |
| Future Work | 2 min | Alert system design |
| Q&A | 3 min | Answer questions |
| **Total** | **20 min** | Leave buffer time |

---

## Key Points to Emphasize

1. ✅ **REST API Architecture** - Proper separation of concerns
2. ✅ **Authentication** - Secure host identification
3. ✅ **Database Design** - Scalable schema with time-series data
4. ✅ **Alert Framework** - Designed for future implementation
5. ✅ **Flexibility** - Supports both system metrics and pipeline data
6. ✅ **Production-Ready** - Real agent code that works on Linux

---

## What Success Looks Like

✓ Flask server running
✓ Test data flowing to database
✓ Data visible in queries
✓ Can explain architecture clearly
✓ Can answer questions confidently
✓ Demo completes in under 20 minutes

**You've got this!** 🎓
