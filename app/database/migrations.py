import os
import sqlite3
from pathlib import Path


def run_migrations(db_path: str) -> None:
    migrations_dir = Path(__file__).parent.parent.parent / "database"
    sql_files = sorted(migrations_dir.glob("*.sql"))

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        for sql_file in sql_files:
            conn.executescript(sql_file.read_text())
        conn.commit()
    finally:
        conn.close()
