from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VENV_DIR = REPO_ROOT / ".venv"
RUNTIME_DIR = REPO_ROOT / "data" / "runtime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap SmartTool-Link on a new machine")
    parser.add_argument("--run", action="store_true", help="Launch the demo stack after setup")
    parser.add_argument("--mode", choices=("auto", "sample", "mqtt"), default="auto")
    parser.add_argument("--skip-pip", action="store_true", help="Skip Python dependency installation")
    parser.add_argument("--skip-build", action="store_true", help="Skip optional C++ CMake build")
    parser.add_argument("--no-venv", action="store_true", help="Use the current interpreter instead of creating .venv")
    parser.add_argument("--init-mysql", action="store_true", help="Attempt MySQL schema initialization after Python setup")
    return parser.parse_args()


def print_step(message: str) -> None:
    print(f"[quickstart] {message}")


def run_command(command: list[str], description: str, env: dict[str, str] | None = None) -> None:
    print_step(description)
    subprocess.run(command, cwd=REPO_ROOT, check=True, env=env)


def copy_example_configs() -> None:
    print_step("Ensuring runtime config files exist")
    mappings = [
        (
            REPO_ROOT / "config" / "app" / "app.example.json",
            REPO_ROOT / "config" / "app" / "app.json",
        ),
        (
            REPO_ROOT / "config" / "mqtt" / "mqtt.example.json",
            REPO_ROOT / "config" / "mqtt" / "mqtt.json",
        ),
        (
            REPO_ROOT / "config" / "database" / "database.example.json",
            REPO_ROOT / "config" / "database" / "database.json",
        ),
    ]
    for source, target in mappings:
        if not target.exists() and source.exists():
            target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            print_step(f"Created {target.relative_to(REPO_ROOT)} from example")


def create_venv() -> None:
    if VENV_DIR.exists():
        print_step("Using existing virtual environment")
        return
    print_step("Creating virtual environment in .venv")
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(VENV_DIR)


def resolve_python(no_venv: bool) -> Path:
    if no_venv:
        return Path(sys.executable)
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def install_python_dependencies(python_exec: Path) -> None:
    run_command([str(python_exec), "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip")
    run_command([str(python_exec), "-m", "pip", "install", "-r", "app/requirements.txt"], "Installing Python dependencies")


def initialize_sqlite(python_exec: Path) -> None:
    run_command([str(python_exec), "scripts/setup/init_db.py"], "Initializing SQLite schema")


def initialize_mysql(python_exec: Path) -> None:
    run_command([str(python_exec), "scripts/setup/init_mysql.py"], "Initializing MySQL schema")


def maybe_build_cpp() -> None:
    cmake_exec = shutil.which("cmake")
    if not cmake_exec:
        print_step("CMake not found. Skipping optional C++ build.")
        return
    run_command([cmake_exec, "-S", ".", "-B", "build"], "Configuring C++ gateway")
    run_command([cmake_exec, "--build", "build"], "Building C++ gateway")


def broker_available() -> bool:
    if shutil.which("mosquitto"):
        return True
    candidates = [
        Path("C:/Program Files/Mosquitto/mosquitto.exe"),
        Path("C:/Program Files (x86)/Mosquitto/mosquitto.exe"),
        Path("/usr/sbin/mosquitto"),
        Path("/usr/local/sbin/mosquitto"),
        Path("/opt/homebrew/sbin/mosquitto"),
        Path("/usr/local/opt/mosquitto/sbin/mosquitto"),
    ]
    return any(path.exists() for path in candidates)


def background_log_path(name: str) -> Path:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DIR / f"{name}.log"


def launch_background_process(command: list[str], log_name: str) -> subprocess.Popen[bytes]:
    log_path = background_log_path(log_name)
    log_handle = open(log_path, "ab")
    if os.name == "nt":
        process = subprocess.Popen(
            command,
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
        )
    else:
        process = subprocess.Popen(
            command,
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    print_step(f"Started {log_name} (pid={process.pid}, log={log_path.relative_to(REPO_ROOT)})")
    return process


def launch_demo_stack(python_exec: Path, mode: str) -> None:
    effective_mode = mode
    if mode == "auto":
        effective_mode = "mqtt" if broker_available() else "sample"

    if effective_mode == "mqtt":
        launch_background_process([str(python_exec), "scripts/run/start_broker.py"], "broker")
        launch_background_process(
            [
                str(python_exec),
                "scripts/run/run_processor.py",
                "--mode",
                "mqtt",
                "--timeout-seconds",
                "86400",
                "--max-messages",
                "1000000",
                "--no-fallback-sample",
            ],
            "processor",
        )
    else:
        run_command([str(python_exec), "scripts/run/run_processor.py", "--mode", "sample"], "Seeding sample telemetry")

    launch_background_process([str(python_exec), "scripts/run/run_dashboard.py"], "dashboard")
    print_step("Demo stack launch requested. Open the latest Streamlit local URL from the dashboard log.")


def print_next_steps(mode: str, used_venv: bool) -> None:
    python_hint = ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"
    if not used_venv:
        python_hint = sys.executable
    print()
    print("Quickstart completed.")
    print(f"Python interpreter: {python_hint}")
    print("Recommended commands:")
    print(f"- {python_hint} scripts/setup/init_db.py")
    if mode == "mqtt":
        print(f"- {python_hint} scripts/run/start_broker.py")
        print(f"- {python_hint} scripts/run/run_processor.py --mode mqtt --timeout-seconds 15")
    else:
        print(f"- {python_hint} scripts/run/run_processor.py --mode sample")
    print(f"- {python_hint} scripts/run/run_dashboard.py")


def main() -> None:
    args = parse_args()
    used_venv = not args.no_venv

    copy_example_configs()

    if used_venv:
        create_venv()

    python_exec = resolve_python(args.no_venv)

    if not args.skip_pip:
        install_python_dependencies(python_exec)

    initialize_sqlite(python_exec)

    if args.init_mysql:
        initialize_mysql(python_exec)

    if not args.skip_build:
        maybe_build_cpp()

    if args.run:
        launch_demo_stack(python_exec, args.mode)

    print_next_steps(args.mode, used_venv)


if __name__ == "__main__":
    main()
