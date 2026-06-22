import sqlite3
from typing import Optional


def insert(db: sqlite3.Connection, customer_name: str, customer_email: str, total_amount: float) -> dict:
    cur = db.execute(
        """
        INSERT INTO orders (customer_name, customer_email, total_amount, status)
        VALUES (?, ?, ?, 'pending')
        """,
        (customer_name, customer_email, total_amount),
    )
    db.execute(
        "INSERT INTO order_status_history (order_id, from_status, to_status) VALUES (?, NULL, 'pending')",
        (cur.lastrowid,),
    )
    db.commit()
    return find_by_id(db, cur.lastrowid)


def find_all(
    db: sqlite3.Connection,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    conditions = []
    params: list = []

    if status and status != "all":
        conditions.append("status = ?")
        params.append(status)
    if search:
        conditions.append("(customer_name LIKE ? OR customer_email LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if date_from:
        conditions.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("created_at < date(?, '+1 day')")
        params.append(date_to)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    total = db.execute(f"SELECT COUNT(*) FROM orders {where}", params).fetchone()[0]
    total_pages = max(1, -(-total // page_size))  # ceiling division
    offset = (page - 1) * page_size

    rows = db.execute(
        f"SELECT * FROM orders {where} ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def find_by_id(db: sqlite3.Connection, order_id: int) -> Optional[dict]:
    row = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    return dict(row) if row else None


def update_status(
    db: sqlite3.Connection, order_id: int, current_status: str, new_status: str
) -> Optional[dict]:
    """Atomic update — only succeeds if current status still matches (optimistic locking)."""
    cur = db.execute(
        """
        UPDATE orders
        SET status = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
        WHERE id = ? AND status = ?
        """,
        (new_status, order_id, current_status),
    )
    if cur.rowcount == 0:
        return None
    db.execute(
        "INSERT INTO order_status_history (order_id, from_status, to_status) VALUES (?, ?, ?)",
        (order_id, current_status, new_status),
    )
    db.commit()
    return find_by_id(db, order_id)


def find_history(db: sqlite3.Connection, order_id: int) -> list:
    rows = db.execute(
        "SELECT * FROM order_status_history WHERE order_id = ? ORDER BY changed_at ASC",
        (order_id,),
    ).fetchall()
    return [dict(r) for r in rows]
