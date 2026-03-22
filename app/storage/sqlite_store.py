from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from typing import Mapping

from ..analytics.health_score import DEFAULT_THRESHOLDS
from ..analytics.health_score import calculate_health_score


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = {
    "device_id": "tool-001",
    "timestamp": "not-generated-yet",
    "metrics": {"temperature": 0.0, "vibration": 0.0, "current": 0.0},
    "health_score": 0.0,
    "anomaly_flag": 0,
}


def load_json_config(primary_relative_path: str, fallback_relative_path: str) -> dict[str, Any]:
    """Load a runtime config file, falling back to the checked-in example."""
    primary_path = REPO_ROOT / primary_relative_path
    fallback_path = REPO_ROOT / fallback_relative_path
    config_path = primary_path if primary_path.exists() else fallback_path
    return json.loads(config_path.read_text(encoding="utf-8"))


def load_database_config() -> dict[str, Any]:
    """Load database configuration with runtime overrides when present."""
    return load_json_config(
        "config/database/database.json",
        "config/database/database.example.json",
    )


def load_app_config() -> dict[str, Any]:
    """Load application runtime settings with example fallback."""
    return load_json_config(
        "config/app/app.json",
        "config/app/app.example.json",
    )


def load_thresholds() -> dict[str, float]:
    """Resolve active alert thresholds from runtime config."""
    configured = dict(load_app_config().get("thresholds", {}))
    thresholds = dict(DEFAULT_THRESHOLDS)
    thresholds.update({key: float(value) for key, value in configured.items()})
    return thresholds


def get_sqlite_db_path() -> Path:
    """Resolve the active SQLite database path from config."""
    database_config = load_database_config()
    sqlite_config = database_config.get("sqlite", {})
    relative_path = sqlite_config.get("path", "data/runtime/smarttool_link.db")
    return (REPO_ROOT / relative_path).resolve()


def initialize_database() -> Path:
    """Create the SQLite database and apply the baseline schema when needed."""
    db_path = get_sqlite_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_path = REPO_ROOT / "sql/schema/init.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(db_path) as connection:
        connection.executescript(schema_sql)

    return db_path


def normalize_telemetry(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize inbound telemetry before persistence and visualization.

    This is where raw readings become business-ready records with thresholds,
    health score, and anomaly flags applied.
    """
    raw_metrics = payload.get("metrics", {})
    thresholds = load_thresholds()
    metrics = {
        "temperature": float(raw_metrics.get("temperature", 0.0)),
        "vibration": float(raw_metrics.get("vibration", 0.0)),
        "current": float(raw_metrics.get("current", 0.0)),
    }

    health_score = float(payload.get("health_score", calculate_health_score(metrics, thresholds=thresholds)))
    anomaly_flag = int(
        any(metrics[name] > thresholds[name] for name in thresholds)
        or health_score < 70.0
    )

    return {
        "device_id": str(payload.get("device_id", "tool-001")),
        "device_name": str(payload.get("device_name", f"Device {payload.get('device_id', 'tool-001')}")),
        "location": str(payload.get("location", "Lab-A")),
        "status": str(payload.get("status", "active")),
        "timestamp": str(payload.get("timestamp", datetime.now(timezone.utc).isoformat())),
        "metrics": metrics,
        "health_score": round(health_score, 2),
        "anomaly_flag": anomaly_flag,
    }


def save_latest_snapshot(payload: Mapping[str, Any]) -> Path:
    """Persist the latest processed telemetry as a local JSON snapshot."""
    output_path = REPO_ROOT / "data/runtime/latest_telemetry.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dict(payload), indent=2), encoding="utf-8")
    return output_path


def persist_sqlite_telemetry(payload: Mapping[str, Any]) -> None:
    """Store one normalized telemetry event and heartbeat into SQLite.

    Besides the telemetry row itself, this function also updates device status
    so the dashboard can render fleet health and current operating state.
    """
    db_path = initialize_database()

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO devices (device_code, name, location, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload["device_id"],
                payload["device_name"],
                payload["location"],
                payload["status"],
            ),
        )
        current_status_row = connection.execute(
            "SELECT status FROM devices WHERE device_code = ?",
            (payload["device_id"],),
        ).fetchone()
        current_status = str(current_status_row[0]) if current_status_row else "active"
        desired_status = str(payload["status"])
        if current_status == "maintenance_review":
            desired_status = current_status
        elif int(payload["anomaly_flag"]) == 1:
            desired_status = "warning"
        elif desired_status not in {"watch", "warning", "maintenance_review"}:
            desired_status = "active"

        connection.execute(
            """
            UPDATE devices
            SET name = ?, location = ?, status = ?
            WHERE device_code = ?
            """,
            (
                payload["device_name"],
                payload["location"],
                desired_status,
                payload["device_id"],
            ),
        )
        connection.execute(
            """
            INSERT INTO telemetry (
                device_code,
                recorded_at,
                temperature,
                vibration,
                current,
                health_score,
                anomaly_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["device_id"],
                payload["timestamp"],
                payload["metrics"]["temperature"],
                payload["metrics"]["vibration"],
                payload["metrics"]["current"],
                payload["health_score"],
                payload["anomaly_flag"],
            ),
        )
        connection.execute(
            """
            INSERT INTO device_heartbeats (device_code, status, heartbeat_at)
            VALUES (?, ?, ?)
            """,
            (
                payload["device_id"],
                desired_status,
                payload["timestamp"],
            ),
        )


def persist_telemetry(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Persist one telemetry event into every configured storage target.

    This is the unified write path used by both sample-mode data and live MQTT
    messages.
    """
    from .mysql_store import mysql_write_enabled
    from .mysql_store import persist_mysql_telemetry

    normalized = normalize_telemetry(payload)

    persist_sqlite_telemetry(normalized)
    if mysql_write_enabled():
        persist_mysql_telemetry(normalized)

    save_latest_snapshot(normalized)
    return normalized


def fetch_latest_telemetry() -> dict[str, Any]:
    """Return the latest telemetry snapshot from SQLite."""
    db_path = initialize_database()

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT
                telemetry.device_code,
                telemetry.recorded_at,
                telemetry.temperature,
                telemetry.vibration,
                telemetry.current,
                telemetry.health_score,
                telemetry.anomaly_flag,
                devices.name,
                devices.location,
                devices.status
            FROM telemetry
            LEFT JOIN devices ON devices.device_code = telemetry.device_code
            ORDER BY recorded_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        return dict(DEFAULT_SNAPSHOT)

    return {
        "device_id": row["device_code"],
        "device_name": row["name"],
        "location": row["location"],
        "status": row["status"],
        "timestamp": row["recorded_at"],
        "metrics": {
            "temperature": row["temperature"],
            "vibration": row["vibration"],
            "current": row["current"],
        },
        "health_score": row["health_score"],
        "anomaly_flag": row["anomaly_flag"],
    }


def fetch_recent_telemetry(limit: int = 20) -> list[dict[str, Any]]:
    """Return recent telemetry history ordered oldest-to-newest for charts."""
    db_path = initialize_database()

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM (
                SELECT device_code, recorded_at, temperature, vibration, current, health_score, anomaly_flag
                FROM telemetry
                ORDER BY recorded_at DESC, id DESC
                LIMIT ?
            ) recent
            ORDER BY recorded_at ASC
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "device_id": row["device_code"],
            "timestamp": row["recorded_at"],
            "temperature": row["temperature"],
            "vibration": row["vibration"],
            "current": row["current"],
            "health_score": row["health_score"],
            "anomaly_flag": row["anomaly_flag"],
        }
        for row in rows
    ]


def fetch_device_overview(limit: int = 12) -> list[dict[str, Any]]:
    """Return fleet-level health, status, and anomaly rollups per device."""
    db_path = initialize_database()

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                devices.device_code,
                devices.name,
                devices.location,
                devices.status,
                COUNT(telemetry.id) AS sample_count,
                ROUND(COALESCE(AVG(telemetry.health_score), 0), 2) AS avg_health_score,
                ROUND(COALESCE(MAX(telemetry.temperature), 0), 2) AS max_temperature,
                COALESCE(MAX(telemetry.recorded_at), devices.created_at) AS last_recorded_at,
                COALESCE(SUM(CASE WHEN telemetry.anomaly_flag = 1 THEN 1 ELSE 0 END), 0) AS anomaly_count,
                maintenance.last_maintenance_at,
                CASE
                    WHEN devices.status = 'active' THEN (
                        SELECT MIN(active_h.heartbeat_at)
                        FROM device_heartbeats active_h
                        WHERE active_h.device_code = devices.device_code
                          AND active_h.status IN ('active', 'healthy')
                          AND active_h.heartbeat_at > COALESCE((
                              SELECT MAX(prev_h.heartbeat_at)
                              FROM device_heartbeats prev_h
                              WHERE prev_h.device_code = devices.device_code
                                AND prev_h.status NOT IN ('active', 'healthy')
                          ), '')
                    )
                    WHEN devices.status = 'warning' THEN (
                        SELECT MIN(warn_h.heartbeat_at)
                        FROM device_heartbeats warn_h
                        WHERE warn_h.device_code = devices.device_code
                          AND warn_h.status = 'warning'
                          AND warn_h.heartbeat_at > COALESCE((
                              SELECT MAX(prev_h.heartbeat_at)
                              FROM device_heartbeats prev_h
                              WHERE prev_h.device_code = devices.device_code
                                AND prev_h.status <> 'warning'
                          ), '')
                    )
                    WHEN devices.status = 'maintenance_review' THEN (
                        SELECT MIN(maint_h.heartbeat_at)
                        FROM device_heartbeats maint_h
                        WHERE maint_h.device_code = devices.device_code
                          AND maint_h.status = 'maintenance_review'
                          AND maint_h.heartbeat_at > COALESCE((
                              SELECT MAX(prev_h.heartbeat_at)
                              FROM device_heartbeats prev_h
                              WHERE prev_h.device_code = devices.device_code
                                AND prev_h.status <> 'maintenance_review'
                          ), '')
                    )
                    ELSE NULL
                END AS status_since
            FROM devices
            LEFT JOIN telemetry ON telemetry.device_code = devices.device_code
            LEFT JOIN (
                SELECT device_code, MAX(created_at) AS last_maintenance_at
                FROM maintenance_logs
                GROUP BY device_code
            ) maintenance ON maintenance.device_code = devices.device_code
            GROUP BY devices.device_code, devices.name, devices.location, devices.status, maintenance.last_maintenance_at, devices.created_at
            ORDER BY last_recorded_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "device_id": row["device_code"],
            "device_name": row["name"],
            "location": row["location"],
            "status": row["status"],
            "sample_count": row["sample_count"],
            "avg_health_score": row["avg_health_score"],
            "max_temperature": row["max_temperature"],
            "last_recorded_at": row["last_recorded_at"],
            "anomaly_count": row["anomaly_count"],
            "last_maintenance_at": row["last_maintenance_at"],
            "status_since": row["status_since"],
        }
        for row in rows
    ]


def fetch_recent_alerts(limit: int = 20) -> list[dict[str, Any]]:
    """Return recent anomalous telemetry events for the alert panel.

    The query also derives whether each alert is still open, acknowledged, or
    already maintained.
    """
    db_path = initialize_database()

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                telemetry.device_code,
                telemetry.recorded_at,
                telemetry.temperature,
                telemetry.vibration,
                telemetry.current,
                telemetry.health_score,
                telemetry.anomaly_flag,
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM maintenance_logs ml
                        WHERE ml.device_code = telemetry.device_code
                          AND ml.created_at >= telemetry.recorded_at
                          AND ml.event_type IN ('MAINTENANCE_COMPLETE', 'RETURN_TO_SERVICE')
                    ) THEN 'maintained'
                    WHEN EXISTS (
                        SELECT 1
                        FROM maintenance_logs ml
                        WHERE ml.device_code = telemetry.device_code
                          AND ml.created_at >= telemetry.recorded_at
                          AND ml.event_type IN ('ACK_ALERT', 'INSPECTION')
                    ) THEN 'acknowledged'
                    ELSE 'unacknowledged'
                END AS alert_state
            FROM telemetry
            WHERE telemetry.anomaly_flag = 1 OR telemetry.health_score < 70
            ORDER BY telemetry.recorded_at DESC, telemetry.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "device_id": row["device_code"],
            "timestamp": row["recorded_at"],
            "temperature": row["temperature"],
            "vibration": row["vibration"],
            "current": row["current"],
            "health_score": row["health_score"],
            "anomaly_flag": row["anomaly_flag"],
            "alert_state": row["alert_state"],
        }
        for row in rows
    ]


def create_maintenance_log(device_id: str, event_type: str, description: str = "") -> dict[str, Any]:
    """Store a maintenance or acknowledgement event and update device status."""
    db_path = initialize_database()
    status_by_event = {
        "ACK_ALERT": "maintenance_review",
        "INSPECTION": "maintenance_review",
        "MAINTENANCE_COMPLETE": "active",
        "RETURN_TO_SERVICE": "active",
    }
    resolved_status = status_by_event.get(event_type, "maintenance_review")
    created_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO devices (device_code, name, location, status)
            VALUES (?, ?, ?, ?)
            """,
            (device_id, f"Device {device_id}", "Lab-A", resolved_status),
        )
        connection.execute(
            """
            UPDATE devices
            SET status = ?
            WHERE device_code = ?
            """,
            (resolved_status, device_id),
        )
        connection.execute(
            """
            INSERT INTO maintenance_logs (device_code, event_type, description, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (device_id, event_type, description, created_at),
        )
        connection.execute(
            """
            INSERT INTO device_heartbeats (device_code, status, heartbeat_at)
            VALUES (?, ?, ?)
            """,
            (device_id, resolved_status, created_at),
        )

    return {
        "device_id": device_id,
        "event_type": event_type,
        "description": description,
        "created_at": created_at,
        "status": resolved_status,
    }


def fetch_recent_maintenance(limit: int = 20, device_id: str | None = None) -> list[dict[str, Any]]:
    """Return recent maintenance and acknowledgement events."""
    db_path = initialize_database()
    query = (
        """
        SELECT device_code, event_type, description, created_at
        FROM maintenance_logs
        {where_clause}
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """
    )
    params: list[Any] = []
    where_clause = ""
    if device_id:
        where_clause = "WHERE device_code = ?"
        params.append(device_id)
    params.append(limit)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query.format(where_clause=where_clause), params).fetchall()

    return [
        {
            "device_id": row["device_code"],
            "event_type": row["event_type"],
            "description": row["description"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
