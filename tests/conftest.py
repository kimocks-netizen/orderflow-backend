import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import get_db
from app.database.migrations import run_migrations
from app.services.auth_service import hash_password


def make_test_db():
    """Return a fresh in-memory DB with migrations + admin user."""
    from pathlib import Path
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    migrations_dir = Path(__file__).parent.parent / "database"
    for sql_file in sorted(migrations_dir.glob("*.sql")):
        conn.executescript(sql_file.read_text())
    conn.execute(
        "INSERT INTO users (email, name, password) VALUES (?, ?, ?)",
        ("admin@orderflow.com", "Admin User", hash_password("password")),
    )
    conn.commit()
    return conn


@pytest.fixture()
def client():
    # Each test gets its own isolated in-memory DB
    db = make_test_db()

    def override_get_db():
        try:
            yield db
        finally:
            pass  # keep open for the test; closed below

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    db.close()


@pytest.fixture()
def auth_headers(client: TestClient):
    res = client.post("/api/auth/login", json={"email": "admin@orderflow.com", "password": "password"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
