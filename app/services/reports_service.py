import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional


def _date_where(date_from: Optional[str], date_to: Optional[str]) -> tuple[str, list]:
    """Return (WHERE clause string, params list) for optional date range."""
    conditions, params = [], []
    if date_from:
        conditions.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("created_at < date(?, '+1 day')")
        params.append(date_to)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params


def get_summary(
    db: sqlite3.Connection,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    where, params = _date_where(date_from, date_to)
    and_ = (" AND " if where else " WHERE ")  # used to append extra conditions

    # ── 30-day trend ──────────────────────────────────────────────────────────
    trend = []
    for i in range(29, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        day_where, day_params = _date_where(
            max(date_from, day) if date_from else day,
            min(date_to, day)   if date_to   else day,
        )
        rows = db.execute(
            f"SELECT status, COUNT(*) as cnt FROM orders {day_where} GROUP BY status",
            day_params,
        ).fetchall()
        counts: dict[str, int] = {"pending": 0, "paid": 0, "shipped": 0, "cancelled": 0}
        for row in rows:
            if row["status"] in counts:
                counts[row["status"]] = row["cnt"]
        trend.append({"date": day, "all": sum(counts.values()), **counts})

    # ── Top 5 customers by order count ───────────────────────────────────────
    top_rows = db.execute(
        f"""
        SELECT customer_name AS name, customer_email AS email,
               COUNT(*) AS orders,
               COALESCE(SUM(CASE WHEN status != 'cancelled' THEN total_amount ELSE 0 END), 0) AS total
        FROM orders {where}
        GROUP BY customer_email
        ORDER BY orders DESC
        LIMIT 5
        """,
        params,
    ).fetchall()
    top_customers = [
        {"name": r["name"], "email": r["email"], "orders": r["orders"], "total": round(r["total"], 2)}
        for r in top_rows
    ]

    # ── Revenue this month vs prev month ──────────────────────────────────────
    now = datetime.now(timezone.utc)
    this_prefix = now.strftime("%Y-%m")
    prev_dt = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc) if now.month > 1 \
        else datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
    prev_prefix = prev_dt.strftime("%Y-%m")

    def month_revenue(prefix: str) -> float:
        row = db.execute(
            f"SELECT COALESCE(SUM(total_amount), 0) FROM orders "
            f"{where}{and_}status != 'cancelled' AND created_at LIKE ?",
            params + [f"{prefix}%"],
        ).fetchone()
        return round(row[0], 2)

    revenue_this_month = month_revenue(this_prefix)
    revenue_prev_month = month_revenue(prev_prefix)

    # ── Cancellation rate ─────────────────────────────────────────────────────
    total = db.execute(f"SELECT COUNT(*) FROM orders {where}", params).fetchone()[0]
    cancelled = db.execute(
        f"SELECT COUNT(*) FROM orders {where}{and_}status = 'cancelled'", params
    ).fetchone()[0]
    cancellation_rate = round((cancelled / total) * 100) if total > 0 else 0

    # ── Avg fulfilment days (created → shipped) ───────────────────────────────
    avg_row = db.execute(
        f"SELECT AVG(CAST((julianday(updated_at) - julianday(created_at)) AS REAL)) "
        f"FROM orders {where}{and_}status = 'shipped'",
        params,
    ).fetchone()
    avg_fulfillment = round(avg_row[0], 1) if avg_row[0] is not None else 0.0

    # ── Peak day ──────────────────────────────────────────────────────────────
    peak_day, peak_count = "", 0
    if trend:
        peak = max(trend, key=lambda d: d["all"])
        peak_day, peak_count = peak["date"], peak["all"]

    return {
        "trend": trend,
        "topCustomers": top_customers,
        "avgFulfillmentDays": avg_fulfillment,
        "cancellationRate": cancellation_rate,
        "revenueThisMonth": revenue_this_month,
        "revenuePrevMonth": revenue_prev_month,
        "peakDay": peak_day,
        "peakDayCount": peak_count,
    }
