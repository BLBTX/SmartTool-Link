CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    location TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_code TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    temperature REAL NOT NULL,
    vibration REAL NOT NULL,
    current REAL NOT NULL,
    health_score REAL NOT NULL,
    anomaly_flag INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (device_code) REFERENCES devices(device_code)
);

CREATE TABLE IF NOT EXISTS device_heartbeats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_code TEXT NOT NULL,
    status TEXT NOT NULL,
    heartbeat_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_code) REFERENCES devices(device_code)
);

CREATE TABLE IF NOT EXISTS maintenance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_code TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_code) REFERENCES devices(device_code)
);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_time
    ON telemetry(device_code, recorded_at);

CREATE INDEX IF NOT EXISTS idx_heartbeat_device_time
    ON device_heartbeats(device_code, heartbeat_at);

INSERT OR IGNORE INTO devices (device_code, name, location, status)
VALUES ('tool-001', 'Demo Power Tool', 'Lab-A', 'active');
