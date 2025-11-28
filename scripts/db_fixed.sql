-- Drop tables in correct order (respecting foreign keys)
DROP TABLE IF EXISTS host_alert_checks;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS alert_types;
DROP TABLE IF EXISTS incoming_data;
DROP TABLE IF EXISTS hosts;

-- Hosts table with host_key for authentication
CREATE TABLE hosts (
  host_id    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  host_name  VARCHAR(255)    NOT NULL,
  host_key   VARCHAR(64)     NOT NULL,              -- Added for API authentication
  os_name    VARCHAR(100)    NULL,
  os_version VARCHAR(50)     NULL,
  is_active  TINYINT(1)      NOT NULL DEFAULT 1,
  last_seen  DATETIME        NULL,                    
  created_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (host_id),
  UNIQUE KEY uq_host_name (host_name),
  UNIQUE KEY uq_host_key (host_key),                 -- Added unique constraint
  KEY ix_last_seen (last_seen)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- Incoming data table (metrics from hosts)
CREATE TABLE incoming_data (
  data_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  host_id         BIGINT UNSIGNED NOT NULL,
  collected_at    DATETIME(3)     NOT NULL,
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  -- Network/OS snapshot
  int_ip          VARCHAR(45)     NULL,
  public_ip       VARCHAR(45)     NULL,
  kernel_name     VARCHAR(50)     NULL,
  kernel_version  VARCHAR(50)     NULL,
  
  -- Core host metrics
  cpu_pct         DECIMAL(5,2)    NULL,
  mem_used_mb     INT UNSIGNED    NULL,
  mem_total_mb    INT UNSIGNED    NULL,
  mem_pct         DECIMAL(5,2)    NULL,
  disk_used_gb    DECIMAL(10,2)   NULL,
  disk_total_gb   DECIMAL(10,2)   NULL,
  disk_pct        DECIMAL(5,2)    NULL,
  
  -- Data-arrival context (for pipeline monitoring)
  dataset_name    VARCHAR(200)    NULL,
  partition_key   VARCHAR(200)    NULL,
  files_count     INT UNSIGNED    NULL,
  size_bytes      BIGINT UNSIGNED NULL,
  min_event_ts    DATETIME        NULL,
  max_event_ts    DATETIME        NULL,
  extra           JSON            NULL,

  PRIMARY KEY (data_id),
  KEY ix_host_time (host_id, collected_at),
  KEY ix_dataset_time (dataset_name, partition_key, collected_at),
  KEY ix_collected_at (collected_at),

  CONSTRAINT fk_incoming_host
    FOREIGN KEY (host_id) REFERENCES hosts(host_id)
      ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- Alert types (catalog of available alert checks)
CREATE TABLE alert_types (
  check_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  check_name       VARCHAR(120)    NOT NULL,
  check_key        VARCHAR(64)     NOT NULL,
  function_name    VARCHAR(100)    NULL,              -- Python function to call
  params_json      JSON            NULL,
  severity         ENUM('L1','L2','L3') NOT NULL DEFAULT 'L1',
  cooldown_minutes INT UNSIGNED    NOT NULL DEFAULT 60,
  enabled          TINYINT(1)      NOT NULL DEFAULT 1,
  notes            VARCHAR(500)    NULL,
  created_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                         ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (check_id),
  UNIQUE KEY uq_check_name (check_name),
  UNIQUE KEY uq_check_key  (check_key)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- Alert instances (actual triggered alerts)
CREATE TABLE alerts (
  alert_id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  host_id         BIGINT UNSIGNED NOT NULL,
  check_id        BIGINT UNSIGNED NOT NULL,
  data_id         BIGINT UNSIGNED NULL,
  triggered_at    DATETIME        NOT NULL,
  severity        ENUM('L1','L2','L3') NOT NULL,
  message         VARCHAR(1000)   NULL,
  status          ENUM('open','acknowledged','resolved')
                                NOT NULL DEFAULT 'open',       
  last_notified_at DATETIME       NULL,
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (alert_id),
  KEY ix_host_status (host_id, status),
  KEY ix_check_status (check_id, status),
  KEY ix_triggered_at (triggered_at),

  CONSTRAINT fk_alert_host
    FOREIGN KEY (host_id) REFERENCES hosts(host_id)
    ON DELETE CASCADE,

  CONSTRAINT fk_alert_check
    FOREIGN KEY (check_id) REFERENCES alert_types(check_id)
    ON DELETE RESTRICT,

  CONSTRAINT fk_alert_data
    FOREIGN KEY (data_id) REFERENCES incoming_data(data_id)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- Host-Alert associations (which alerts are enabled for which hosts)
CREATE TABLE host_alert_checks (
    association_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    host_id BIGINT UNSIGNED NOT NULL,
    check_id BIGINT UNSIGNED NOT NULL,
    enabled TINYINT(1) DEFAULT 1,
    params_json JSON,                                  -- Host-specific parameters
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uq_host_check (host_id, check_id),
    FOREIGN KEY (host_id) REFERENCES hosts(host_id) ON DELETE CASCADE,
    FOREIGN KEY (check_id) REFERENCES alert_types(check_id) ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- Insert sample alert types
INSERT INTO alert_types (check_name, check_key, function_name, params_json, severity, notes) VALUES
('Host Online', 'host_online', 'check_host_online', '{"offline_threshold_minutes": 60}', 'L1', 'Checks if host has sent data recently'),
('Disk Space', 'disk_space', 'check_disk_space', '{"threshold_pct": 90}', 'L2', 'Alerts when disk usage exceeds threshold'),
('Memory Usage', 'memory_usage', 'check_memory_usage', '{"threshold_pct": 90}', 'L2', 'Alerts when memory usage exceeds threshold');

-- Insert a test host with a simple key (use a real hash in production)
INSERT INTO hosts (host_name, host_key, os_name, os_version, is_active, last_seen) VALUES
('test-host', 'test-key-123', 'Unknown', 'Unknown', 1, NOW());
