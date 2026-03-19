from __future__ import annotations

import argparse
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.storage.sqlite_store import get_sqlite_db_path
from app.storage.sqlite_store import initialize_database


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


def main() -> None:
    """Run an end-to-end test from the C++ gateway into the Python processor."""
    parser = argparse.ArgumentParser(description="Run the C++ gateway MQTT integration test")
    parser.add_argument(
        "--gateway-path",
        default="build/Debug/smarttool_gateway.exe",
        help="Path to the gateway executable to test",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=2.5,
        help="Seconds to wait for the processor subscription before launching the gateway",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    before_count = telemetry_count()

    broker = None
    if not port_open("127.0.0.1", 1883):
        broker = subprocess.Popen([sys.executable, "scripts/run/start_broker.py"], cwd=repo_root)
    try:
        time.sleep(1.5)

        processor = subprocess.Popen(
            [
                sys.executable,
                "scripts/run/run_processor.py",
                "--mode",
                "mqtt",
                "--timeout-seconds",
                "20",
                "--max-messages",
                "3",
                "--no-fallback-sample",
            ],
            cwd=repo_root,
        )
        try:
            time.sleep(args.settle_seconds)
            gateway_run = subprocess.run(
                [args.gateway_path],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            if gateway_run.stdout:
                print(gateway_run.stdout, end="")
            if gateway_run.stderr:
                print(gateway_run.stderr, end="", file=sys.stderr)
            if gateway_run.returncode != 0:
                raise RuntimeError(f"Gateway exited with code {gateway_run.returncode}")
            processor_exit = processor.wait(timeout=20)
            if processor_exit != 0:
                raise RuntimeError(f"Processor exited with code {processor_exit}")
        finally:
            if processor.poll() is None:
                processor.terminate()
                processor.wait(timeout=5)

        after_count = telemetry_count()
        if after_count - before_count < 3:
            raise RuntimeError("Expected at least 3 new telemetry rows from the C++ gateway flow.")

        print(f"C++ gateway MQTT test passed. Database: {get_sqlite_db_path()}")
    finally:
        if broker is not None:
            broker.terminate()
            try:
                broker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                broker.kill()


if __name__ == "__main__":
    main()
