from __future__ import annotations

import subprocess
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def main() -> None:
    """Launch the Streamlit dashboard with the project entrypoint."""
    dashboard_path = Path("app/dashboard/main.py")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(dashboard_path),
            "--server.headless",
            "true",
            "--browser.gatherUsageStats",
            "false",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
