from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def resolve_mosquitto() -> str:
    """Resolve the local mosquitto broker executable."""
    env_path = os.environ.get("SMARTTOOL_MOSQUITTO_EXE")
    if env_path:
        return env_path

    path_hit = shutil.which("mosquitto")
    if path_hit:
        return path_hit

    candidates = [
        Path("C:/Program Files/Mosquitto/mosquitto.exe"),
        Path("C:/Program Files (x86)/Mosquitto/mosquitto.exe"),
        Path("/usr/sbin/mosquitto"),
        Path("/usr/local/sbin/mosquitto"),
        Path("/opt/homebrew/sbin/mosquitto"),
        Path("/usr/local/opt/mosquitto/sbin/mosquitto"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        "Mosquitto executable not found. Install Mosquitto or set SMARTTOOL_MOSQUITTO_EXE."
    )


def main() -> None:
    """Start a local Mosquitto broker using the repository config."""
    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "config/mqtt/mosquitto.conf"
    subprocess.run([resolve_mosquitto(), "-c", str(config_path), "-v"], check=True)


if __name__ == "__main__":
    main()
