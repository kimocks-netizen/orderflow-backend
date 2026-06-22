#!/usr/bin/env python3
"""
Seed the database with 1 admin user and 500 orders.
Run: python seed.py
"""
import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.database.migrations import run_migrations
from app.services.auth_service import hash_password

STATUSES = ["pending", "paid", "shipped", "cancelled"]
STATUS_WEIGHTS = [0.25, 0.30, 0.30, 0.15]

TRANSITIONS = {
    "pending":   ["paid", "cancelled"],
    "paid":      ["shipped", "cancelled"],
    "shipped":   [],
    "cancelled": [],
}

FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Eva", "Frank", "Grace", "Henry",
               "Iris", "Jack", "Karen", "Leo", "Mia", "Noah", "Olivia", "Paul",
               "Quinn", "Rachel", "Sam", "Tina", "Uma", "Victor", "Wendy", "Xander",
               "Yara", "Zoe", "Aaron", "Beth", "Chris", "Diana"]
LAST_NAMES  = ["Johnson", "Smith", "White", "Brown", "Martinez", "Lee", "Kim",
               "Davis", "Wilson", "Taylor", "Garcia", "Anderson", "Thomas", "Jackson",
               "Harris", "Martin", "Thompson", "Moore", "Young", "Allen"]
DOMAINS     = ["example.com", "mail.com", "test.org", "demo.io", "sample.net"]


def rand_name() -> tuple[str, str]:
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    return fn, ln


def rand_email(fn: str, ln: str) -> str:
    return f"{fn.lower()}.{ln.lower()}{random.randint(1, 99)}@{random.choice(DOMAINS)}"


def rand_date(days_ago_max: int = 60) -> str:
    offset = random.randint(0, days_ago_max * 24 * 3600)
    dt = datetime.now(timezone.utc) - timedelta(seconds=offset)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_history(order_id: int, status: str, created_at: str) -> list[tuple]:
    """Build a realistic status history chain ending at the given status."""
    chain = ["pending"]
    current = "pending"
    while current != status:
        nexts = TRANSITIONS[current]
        if not nexts:
            break
        # Bias towards the target status
        if status in nexts:
            current = status
        else:
            current = nexts[0]
        chain.append(current)

    entries = []
    ts = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    prev = None
    for step in chain:
        changed_at = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        entries.append((order_id, prev, step, changed_at))
        prev = step
        ts += timedelta(hours=random.randint(1, 48))
    return entries


def seed():
    settings = get_settings()
    run_migrations(settings.database_path)

    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    # ── Admin user ────────────────────────────────────────────────────────────
    existing = conn.execute("SELECT id FROM users WHERE email = 'admin@orderflow.com'").fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (email, name, password) VALUES (?, ?, ?)",
            ("admin@orderflow.com", "Admin User", hash_password("password")),
        )
        print("✓ Admin user created  (admin@orderflow.com / password)")
    else:
        print("✓ Admin user already exists — skipping")

    # ── Orders ────────────────────────────────────────────────────────────────
    existing_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if existing_count >= 500:
        print(f"✓ Orders already seeded ({existing_count} rows) — skipping")
        conn.close()
        return

    orders_to_seed = 500 - existing_count
    print(f"  Seeding {orders_to_seed} orders…")

    for _ in range(orders_to_seed):
        fn, ln = rand_name()
        email       = rand_email(fn, ln)
        amount      = round(random.uniform(10.0, 999.99), 2)
        status      = random.choices(STATUSES, STATUS_WEIGHTS)[0]
        created_at  = rand_date(60)
        updated_at  = created_at

        cur = conn.execute(
            """
            INSERT INTO orders (customer_name, customer_email, total_amount, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (f"{fn} {ln}", email, amount, status, created_at, updated_at),
        )
        order_id = cur.lastrowid

        for entry in build_history(order_id, status, created_at):
            conn.execute(
                "INSERT INTO order_status_history (order_id, from_status, to_status, changed_at) VALUES (?, ?, ?, ?)",
                entry,
            )

    conn.commit()
    conn.close()
    print(f"✓ Seeded {orders_to_seed} orders successfully")


if __name__ == "__main__":
    seed()
