import sqlite3
from typing import Optional

from app.repositories import order_repository
from app.errors.exceptions import ValidationError, NotFoundError, ConflictError

ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    "pending":   ["paid", "cancelled"],
    "paid":      ["shipped", "cancelled"],
    "shipped":   [],
    "cancelled": [],
}


def get_orders(
    db: sqlite3.Connection,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict:
    return order_repository.find_all(
        db, page=page, page_size=page_size,
        status=status, search=search,
        date_from=date_from, date_to=date_to,
    )


def get_order(db: sqlite3.Connection, order_id: int) -> dict:
    order = order_repository.find_by_id(db, order_id)
    if not order:
        raise NotFoundError(f"Order {order_id} not found")
    return order


def create_order(
    db: sqlite3.Connection,
    customer_name: str,
    customer_email: str,
    total_amount: float,
) -> dict:
    return order_repository.insert(db, customer_name, customer_email, total_amount)


def update_status(db: sqlite3.Connection, order_id: int, new_status: str) -> dict:
    order = order_repository.find_by_id(db, order_id)
    if not order:
        raise NotFoundError(f"Order {order_id} not found")

    current = order["status"]
    allowed = ALLOWED_TRANSITIONS.get(current, [])
    if new_status not in allowed:
        raise ValidationError(
            f"Cannot transition from '{current}' to '{new_status}'. "
            f"Allowed: {allowed or 'none (terminal state)'}"
        )

    updated = order_repository.update_status(db, order_id, current, new_status)
    if not updated:
        raise ConflictError("Order status was changed by another request. Please refresh and try again.")
    return updated


def get_history(db: sqlite3.Connection, order_id: int) -> list:
    if not order_repository.find_by_id(db, order_id):
        raise NotFoundError(f"Order {order_id} not found")
    return order_repository.find_history(db, order_id)
