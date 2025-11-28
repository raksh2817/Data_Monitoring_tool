-- Setup alert associations for test hosts
-- This configures which alerts are enabled for which hosts

-- First, verify alert types exist
SELECT 'Available Alert Types:' as '';
SELECT check_id, check_name, check_key, function_name FROM alert_types;

-- Associate alerts with hosts
-- Each host can have different thresholds

-- web-server-01: Monitor all metrics with normal thresholds
INSERT INTO host_alert_checks (host_id, check_id, enabled, params_json)
SELECT h.host_id, at.check_id, 1,
    CASE at.check_key
        WHEN 'host_online' THEN '{"offline_threshold_minutes": 60}'
        WHEN 'disk_space' THEN '{"threshold_pct": 85}'
        WHEN 'memory_usage' THEN '{"threshold_pct": 85}'
    END
FROM hosts h
CROSS JOIN alert_types at
WHERE h.host_name = 'web-server-01' 
  AND at.check_key IN ('host_online', 'disk_space', 'memory_usage')
ON DUPLICATE KEY UPDATE enabled=1;

-- api-server-02: High CPU server - monitor CPU + standard checks
INSERT INTO host_alert_checks (host_id, check_id, enabled, params_json)
SELECT h.host_id, at.check_id, 1,
    CASE at.check_key
        WHEN 'host_online' THEN '{"offline_threshold_minutes": 60}'
        WHEN 'disk_space' THEN '{"threshold_pct": 85}'
        WHEN 'memory_usage' THEN '{"threshold_pct": 85}'
    END
FROM hosts h
CROSS JOIN alert_types at
WHERE h.host_name = 'api-server-02'
  AND at.check_key IN ('host_online', 'disk_space', 'memory_usage')
ON DUPLICATE KEY UPDATE enabled=1;

-- db-server-03: High memory server - monitor memory more strictly
INSERT INTO host_alert_checks (host_id, check_id, enabled, params_json)
SELECT h.host_id, at.check_id, 1,
    CASE at.check_key
        WHEN 'host_online' THEN '{"offline_threshold_minutes": 60}'
        WHEN 'disk_space' THEN '{"threshold_pct": 85}'
        WHEN 'memory_usage' THEN '{"threshold_pct": 80}'  -- Stricter threshold
    END
FROM hosts h
CROSS JOIN alert_types at
WHERE h.host_name = 'db-server-03'
  AND at.check_key IN ('host_online', 'disk_space', 'memory_usage')
ON DUPLICATE KEY UPDATE enabled=1;

-- storage-server-04: High disk server - monitor disk more strictly
INSERT INTO host_alert_checks (host_id, check_id, enabled, params_json)
SELECT h.host_id, at.check_id, 1,
    CASE at.check_key
        WHEN 'host_online' THEN '{"offline_threshold_minutes": 60}'
        WHEN 'disk_space' THEN '{"threshold_pct": 80}'  -- Stricter threshold
        WHEN 'memory_usage' THEN '{"threshold_pct": 85}'
    END
FROM hosts h
CROSS JOIN alert_types at
WHERE h.host_name = 'storage-server-04'
  AND at.check_key IN ('host_online', 'disk_space', 'memory_usage')
ON DUPLICATE KEY UPDATE enabled=1;

-- Verify associations were created
SELECT '' as '';
SELECT 'Alert Associations Created:' as '';
SELECT 
    h.host_name,
    at.check_name,
    hac.enabled,
    hac.params_json
FROM host_alert_checks hac
JOIN hosts h ON hac.host_id = h.host_id
JOIN alert_types at ON hac.check_id = at.check_id
ORDER BY h.host_name, at.check_name;

-- Show counts
SELECT '' as '';
SELECT 'Summary:' as '';
SELECT 
    h.host_name,
    COUNT(*) as alert_checks_enabled
FROM host_alert_checks hac
JOIN hosts h ON hac.host_id = h.host_id
WHERE hac.enabled = 1
GROUP BY h.host_name;
