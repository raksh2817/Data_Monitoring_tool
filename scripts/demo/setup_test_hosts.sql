-- Setup script for test hosts
-- Run this BEFORE running the test scripts

-- First, make sure the test host from earlier exists
INSERT INTO hosts (host_name, host_key, os_name, os_version, is_active, last_seen) 
VALUES ('web-server-01', 'test-key-123', 'Linux', '22.04', 1, NOW())
ON DUPLICATE KEY UPDATE host_key='test-key-123';

-- Add test hosts for different scenarios
INSERT INTO hosts (host_name, host_key, os_name, os_version, is_active, last_seen) 
VALUES 
    ('api-server-02', 'high-cpu-server', 'Linux', '22.04', 1, NOW()),
    ('db-server-03', 'high-mem-server', 'Linux', '20.04', 1, NOW()),
    ('storage-server-04', 'high-disk-server', 'Linux', '22.04', 1, NOW())
ON DUPLICATE KEY UPDATE is_active=1;

-- Verify hosts were created
SELECT host_id, host_name, host_key, is_active FROM hosts;

-- Show count
SELECT COUNT(*) as total_hosts FROM hosts WHERE is_active=1;

