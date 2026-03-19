USE smarttool_link$$

DROP PROCEDURE IF EXISTS sp_upsert_device$$
CREATE PROCEDURE sp_upsert_device(
    IN in_device_code VARCHAR(64),
    IN in_name VARCHAR(128),
    IN in_location VARCHAR(128),
    IN in_status VARCHAR(32)
)
BEGIN
    INSERT INTO devices (device_code, name, location, status)
    VALUES (in_device_code, in_name, in_location, in_status)
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        location = VALUES(location),
        status = VALUES(status);
END$$

DROP PROCEDURE IF EXISTS sp_insert_telemetry$$
CREATE PROCEDURE sp_insert_telemetry(
    IN in_device_code VARCHAR(64),
    IN in_recorded_at DATETIME,
    IN in_temperature DOUBLE,
    IN in_vibration DOUBLE,
    IN in_current_value DOUBLE,
    IN in_health_score DOUBLE,
    IN in_anomaly_flag TINYINT
)
BEGIN
    INSERT INTO telemetry (
        device_code,
        recorded_at,
        temperature,
        vibration,
        current_value,
        health_score,
        anomaly_flag
    ) VALUES (
        in_device_code,
        in_recorded_at,
        in_temperature,
        in_vibration,
        in_current_value,
        in_health_score,
        in_anomaly_flag
    );

    INSERT INTO device_heartbeats (device_code, status, heartbeat_at)
    VALUES (
        in_device_code,
        IF(in_anomaly_flag = 1, 'warning', 'healthy'),
        in_recorded_at
    );
END$$

DROP PROCEDURE IF EXISTS sp_device_health_overview$$
CREATE PROCEDURE sp_device_health_overview(IN in_device_code VARCHAR(64))
BEGIN
    SELECT
        device_code,
        COUNT(*) AS sample_count,
        ROUND(AVG(health_score), 2) AS avg_health_score,
        MAX(recorded_at) AS last_recorded_at,
        SUM(CASE WHEN anomaly_flag = 1 THEN 1 ELSE 0 END) AS anomaly_count
    FROM telemetry
    WHERE device_code = in_device_code
    GROUP BY device_code;
END$$
