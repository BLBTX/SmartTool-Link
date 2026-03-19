from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def load_config() -> dict[str, Any]:
    """Load MySQL connection settings from the runtime config."""
    repo_root = Path(__file__).resolve().parents[2]
    primary_path = repo_root / "config/database/database.json"
    fallback_path = repo_root / "config/database/database.example.json"
    config_path = primary_path if primary_path.exists() else fallback_path
    return json.loads(config_path.read_text(encoding="utf-8"))


def main() -> None:
    """Initialize the MySQL schema when a server is available."""
    try:
        mysql_connector = importlib.import_module("mysql.connector")
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            "mysql-connector-python is not installed. Run 'pip install -r app/requirements.txt'."
        ) from error

    repo_root = Path(__file__).resolve().parents[2]
    config = load_config()
    mysql_config = dict(config.get("mysql") or {})

    try:
        connection = mysql_connector.connect(
            host=mysql_config.get("host", "127.0.0.1"),
            port=int(mysql_config.get("port", 3306)),
            user=mysql_config.get("user", "root"),
            password=mysql_config.get("password", ""),
        )
    except Exception as error:
        raise RuntimeError(
            "Unable to connect to MySQL. Start a MySQL server or update config/database/database.json."
        ) from error

    try:
        schema_sql = (repo_root / "sql/schema/init_mysql.sql").read_text(encoding="utf-8")
        procedures_sql = (repo_root / "sql/procedures/telemetry_mysql.sql").read_text(encoding="utf-8")
        cursor = connection.cursor()
        for statement in [chunk.strip() for chunk in schema_sql.split(";") if chunk.strip()]:
            cursor.execute(statement)
        for statement in [chunk.strip() for chunk in procedures_sql.split("$$") if chunk.strip()]:
            cursor.execute(statement)
        connection.commit()
        print("Initialized MySQL schema for smarttool_link")
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(error)
        raise SystemExit(1)
