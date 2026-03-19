CREATE DATABASE IF NOT EXISTS smarttool_link
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smarttool_link;

CREATE TABLE IF NOT EXISTS devices (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    location VARCHAR(128),
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS telemetry (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_code VARCHAR(64) NOT NULL,
    recorded_at DATETIME NOT NULL,
    temperature DOUBLE NOT NULL,
    vibration DOUBLE NOT NULL,
    current_value DOUBLE NOT NULL,
    health_score DOUBLE NOT NULL,
    anomaly_flag TINYINT(1) NOT NULL DEFAULT 0,
    CONSTRAINT fk_telemetry_device
        FOREIGN KEY (device_code) REFERENCES devices(device_code)
);

CREATE TABLE IF NOT EXISTS device_heartbeats (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_code VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    heartbeat_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_heartbeats_device
        FOREIGN KEY (device_code) REFERENCES devices(device_code)
);

CREATE TABLE IF NOT EXISTS maintenance_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    device_code VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_maintenance_device
        FOREIGN KEY (device_code) REFERENCES devices(device_code)
);

CREATE INDEX idx_telemetry_device_time
    ON telemetry(device_code, recorded_at);

CREATE INDEX idx_heartbeat_device_time
    ON device_heartbeats(device_code, heartbeat_at);

INSERT INTO devices (device_code, name, location, status)
VALUES ('tool-001', 'Demo Power Tool', 'Lab-A', 'active')
ON DUPLICATE KEY UPDATE name = VALUES(name), location = VALUES(location), status = VALUES(status);
