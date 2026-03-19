from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.storage.sqlite_store import initialize_database


def main() -> None:
    """Initialize the local SQLite database schema for development."""
    db_path = initialize_database()
    print(f"Initialized database at: {db_path}")


if __name__ == "__main__":
    main()
