import sqlite3
from typing import Optional


def find_by_email(db: sqlite3.Connection, email: str) -> Optional[dict]:
    row = db.execute(
        "SELECT id, email, name, password FROM users WHERE email = ?", (email,)
    ).fetchone()
    return dict(row) if row else None
