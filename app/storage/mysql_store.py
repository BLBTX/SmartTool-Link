from __future__ import annotations

import importlib
from typing import Any
from typing import Mapping

from .sqlite_store import load_database_config


def mysql_write_enabled() -> bool:
    """Return whether MySQL mirroring is enabled in runtime config."""
    config = load_database_config()
    targets = [str(item).lower() for item in config.get("write_targets", ["sqlite"])]
    return "mysql" in targets


def _load_mysql_connector() -> Any:
    """Load the MySQL connector only when MySQL persistence is enabled."""
    try:
        return importlib.import_module("mysql.connector")
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "mysql-connector-python is not installed. Run 'pip install -r app/requirements.txt'."
        ) from error


def _connect_mysql() -> Any:
    """Open a MySQL connection from runtime config."""
    connector = _load_mysql_connector()
    config = load_database_config()
    mysql_config = dict(config.get("mysql") or {})
    return connector.connect(
        host=mysql_config.get("host", "127.0.0.1"),
        port=int(mysql_config.get("port", 3306)),
        user=mysql_config.get("user", "root"),
        password=mysql_config.get("password", ""),
        database=mysql_config.get("database", "smarttool_link"),
    )


def persist_mysql_telemetry(payload: Mapping[str, Any]) -> None:
    """Mirror one normalized telemetry event into MySQL when enabled."""
    connection = _connect_mysql()
    try:
        cursor = connection.cursor()
        try:
            cursor.callproc(
                "sp_upsert_device",
                (
                    payload["device_id"],
                    payload.get("device_name", f"Device {payload['device_id']}"),
                    payload.get("location", "Lab-A"),
                    payload.get("status", "active"),
                ),
            )
        except Exception:
            cursor.execute(
                """
                INSERT INTO devices (device_code, name, location, status)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    location = VALUES(location),
                    status = VALUES(status)
                """,
                (
                    payload["device_id"],
                    payload.get("device_name", f"Device {payload['device_id']}"),
                    payload.get("location", "Lab-A"),
                    payload.get("status", "active"),
                ),
            )

        try:
            cursor.callproc(
                "sp_insert_telemetry",
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
        except Exception:
            cursor.execute(
                """
                INSERT INTO telemetry (
                    device_code,
                    recorded_at,
                    temperature,
                    vibration,
                    current_value,
                    health_score,
                    anomaly_flag
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
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
            cursor.execute(
                """
                INSERT INTO device_heartbeats (device_code, status, heartbeat_at)
                VALUES (%s, %s, %s)
                """,
                (
                    payload["device_id"],
                    "warning" if payload["anomaly_flag"] else "healthy",
                    payload["timestamp"],
                ),
            )

        connection.commit()
    finally:
        connection.close()
