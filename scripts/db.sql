

DROP TABLE IF EXISTS hosts;
CREATE TABLE hosts (
  host_id    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  host_name  VARCHAR(255)    NOT NULL,                 -- host name
  os_name    VARCHAR(100)    NULL,                     -- e.g., Operating system name
  os_version VARCHAR(50)     NULL,                     -- e.g., 22.04, 2019
  is_active  TINYINT(1)      NOT NULL DEFAULT 1,
  last_seen  DATETIME        NULL,                    
  created_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (host_id),
  UNIQUE KEY uq_host_name (host_name),                 -- keep one row per host name
  KEY ix_last_seen (last_seen)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS incoming_data;
CREATE TABLE incoming_data (
  data_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  host_id         BIGINT UNSIGNED NOT NULL,          -- FK → hosts.host_id
  collected_at    DATETIME(3)     NOT NULL,          -- measurement time (ms precision)
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  -- Network/OS snapshot (lightweight)
  int_ip          VARCHAR(45)     NULL,
  public_ip       VARCHAR(45)     NULL,
  kernel_name     VARCHAR(50)     NULL,              -- e.g., "Linux", "Windows NT"
  kernel_version  VARCHAR(50)     NULL,              
  -- Core host metrics
  cpu_pct         DECIMAL(5,2)    NULL,              -- 0–100
  mem_used_mb     INT UNSIGNED    NULL,
  mem_total_mb    INT UNSIGNED    NULL,
  mem_pct         DECIMAL(5,2)    NULL,              -- convenience
  disk_used_gb    DECIMAL(10,2)   NULL,
  disk_total_gb   DECIMAL(10,2)   NULL,
  disk_pct        DECIMAL(5,2)    NULL,              -- convenience
  -- Data-arrival context (only populated for arrival records)
  dataset_name    VARCHAR(200)    NULL,
  partition_key   VARCHAR(200)    NULL,
  files_count     INT UNSIGNED    NULL,
  size_bytes      BIGINT UNSIGNED NULL,
  min_event_ts    DATETIME        NULL,
  max_event_ts    DATETIME        NULL,
  extra           JSON            NULL,               -- future-proofing

  PRIMARY KEY (data_id),

  -- Time-series & query patterns
  KEY ix_host_time (host_id, collected_at),
  KEY ix_dataset_time (dataset_name, partition_key, collected_at),
  KEY ix_collected_at (collected_at),

  CONSTRAINT fk_incoming_host
    FOREIGN KEY (host_id) REFERENCES hosts(host_id)
      ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;



-- Alert check catalog: defines WHAT to alert on (logic lives in code)
DROP TABLE IF EXISTS alert_types;
CREATE TABLE alert_types (
  check_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  check_name       VARCHAR(120)    NOT NULL,     -- human-friendly name (unique)
  check_key        VARCHAR(64)     NOT NULL,     -- short key used in code: e.g. 'low_mem','low_disk','file_missing'
  params_json      JSON            NULL,         -- optional params, e.g. {"threshold_pct":90,"window_minutes":5,"agg":"avg"}
  severity         ENUM('L1','L2','L3') NOT NULL DEFAULT 'L1',
  cooldown_minutes INT UNSIGNED    NOT NULL DEFAULT 60,  -- suppress repeat alerts
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



-- One row per alert occurrence
DROP TABLE IF EXISTS alerts;
CREATE TABLE alerts (
  alert_id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- Relationships
  host_id         BIGINT UNSIGNED NOT NULL,   -- FK → hosts.host_id
  check_id        BIGINT UNSIGNED NOT NULL,   -- FK → alert_checks.check_id
  data_id         BIGINT UNSIGNED NULL,       -- FK → incoming_data.data_id 

  -- State
  triggered_at    DATETIME        NOT NULL,   -- when the condition was detected
  severity        ENUM('L1','L2','L3') NOT NULL,
  message         VARCHAR(1000)   NULL,       -- rendered message (optional)
  status          ENUM('open','acknowledged','resolved')
                                NOT NULL DEFAULT 'open',       
  last_notified_at DATETIME       NULL,       -- throttling/notification tracking
  created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (alert_id),

  KEY ix_host_status (host_id, status),
  KEY ix_check_status (check_id, status),
  KEY ix_triggered_at (triggered_at),

  -- Foreign keys
  CONSTRAINT fk_alert_host
    FOREIGN KEY (host_id) REFERENCES hosts(host_id)
    ON DELETE CASCADE,

  CONSTRAINT fk_alert_check
    FOREIGN KEY (check_id) REFERENCES alert_checks(check_id)
    ON DELETE RESTRICT,

  CONSTRAINT fk_alert_data
    FOREIGN KEY (data_id) REFERENCES incoming_data(data_id)
    ON DELETE SET NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


CREATE TABLE host_alert_checks (
    association_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    host_id BIGINT UNSIGNED NOT NULL,
    check_id BIGINT UNSIGNED NOT NULL,
    enabled TINYINT(1) DEFAULT 1,
    params_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (host_id) REFERENCES hosts(host_id),
    FOREIGN KEY (check_id) REFERENCES alert_checks(check_id)
);
