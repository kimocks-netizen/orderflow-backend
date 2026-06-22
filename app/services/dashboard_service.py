import sqlite3
from datetime import datetime, timedelta, timezone


def get_summary(db: sqlite3.Connection) -> dict:
    # Orders by status
    rows = db.execute(
        "SELECT status, COUNT(*) as cnt FROM orders GROUP BY status"
    ).fetchall()
    by_status = {"pending": 0, "paid": 0, "shipped": 0, "cancelled": 0}
    for row in rows:
        by_status[row["status"]] = row["cnt"]

    total_orders = sum(by_status.values())

    # Revenue (exclude cancelled)
    rev_row = db.execute(
        "SELECT COALESCE(SUM(total_amount), 0), COUNT(*) FROM orders WHERE status != 'cancelled'"
    ).fetchone()
    total_revenue = rev_row[0]
    revenue_count = rev_row[1]
    avg_order_value = (total_revenue / revenue_count) if revenue_count > 0 else 0.0

    # Orders today (UTC)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    orders_today = db.execute(
        "SELECT COUNT(*) FROM orders WHERE created_at >= ?", (today,)
    ).fetchone()[0]

    # Orders per day — last 7 days
    orders_per_day = []
    for i in range(6, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        count = db.execute(
            "SELECT COUNT(*) FROM orders WHERE created_at >= ? AND created_at < date(?, '+1 day')",
            (day, day),
        ).fetchone()[0]
        orders_per_day.append({"date": day, "count": count})

    return {
        "total_orders": total_orders,
        "orders_by_status": by_status,
        "total_revenue": round(total_revenue, 2),
        "avg_order_value": round(avg_order_value, 2),
        "orders_today": orders_today,
        "orders_per_day": orders_per_day,
    }
