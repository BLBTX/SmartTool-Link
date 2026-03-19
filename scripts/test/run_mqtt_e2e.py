from __future__ import annotations

import json
import socket
import sqlite3
import subprocess
import sys
import time
from typing import Any
from pathlib import Path

import paho.mqtt.client as mqtt

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.storage.sqlite_store import get_sqlite_db_path
from app.storage.sqlite_store import initialize_database


def wait_for_port(host: str, port: int, timeout_seconds: float) -> None:
    """Wait until a TCP port starts accepting connections."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.2)
    raise TimeoutError(f"Timed out waiting for {host}:{port}")


def telemetry_count() -> int:
    """Return the current telemetry row count for validation."""
    db_path = initialize_database()
    with sqlite3.connect(db_path) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0])


def port_open(host: str, port: int) -> bool:
    """Return whether a TCP endpoint is already accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def publish_sample_messages() -> None:
    """Publish a short telemetry burst into the local MQTT broker."""
    client = create_mqtt_client("smarttool-e2e")
    client.connect("127.0.0.1", 1883, keepalive=30)
    for index in range(3):
        payload = {
            "device_id": "tool-e2e",
            "timestamp": f"2026-03-18T05:00:0{index}Z",
            "metrics": {
                "temperature": 40.0 + index,
                "vibration": 2.5 + index * 0.1,
                "current": 8.0 + index * 0.2,
            },
        }
        client.publish("smarttool/devices/telemetry", json.dumps(payload), qos=1)
    client.disconnect()


def create_mqtt_client(client_id: str) -> Any:
    """Create a compatible MQTT client across paho callback API variants."""
    try:
        callback_api = getattr(mqtt, "CallbackAPIVersion")
        return mqtt.Client(callback_api_version=callback_api.VERSION2, client_id=client_id)
    except (AttributeError, TypeError):
        return mqtt.Client(client_id=client_id)


def main() -> None:
    """Run a local broker-to-processor MQTT integration test."""
    repo_root = Path(__file__).resolve().parents[2]
    before_count = telemetry_count()

    broker = None
    if not port_open("127.0.0.1", 1883):
        broker = subprocess.Popen([sys.executable, "scripts/run/start_broker.py"], cwd=repo_root)
    try:
        wait_for_port("127.0.0.1", 1883, timeout_seconds=10)

        processor = subprocess.Popen(
            [
                sys.executable,
                "scripts/run/run_processor.py",
                "--mode",
                "mqtt",
                "--timeout-seconds",
                "15",
                "--max-messages",
                "3",
                "--no-fallback-sample",
            ],
            cwd=repo_root,
        )
        try:
            time.sleep(1.0)
            publish_sample_messages()
            processor_exit = processor.wait(timeout=20)
            if processor_exit != 0:
                raise RuntimeError(f"Processor exited with code {processor_exit}")
        finally:
            if processor.poll() is None:
                processor.terminate()
                processor.wait(timeout=5)

        after_count = telemetry_count()
        if after_count - before_count < 3:
            raise RuntimeError("Expected at least 3 new telemetry rows from MQTT flow.")

        db_path = get_sqlite_db_path()
        print(f"MQTT end-to-end test passed. Database: {db_path}")
    finally:
        if broker is not None:
            broker.terminate()
            try:
                broker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                broker.kill()


if __name__ == "__main__":
    main()
