import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.database.connection import get_db
from app.core.security import get_current_user
from app.schemas.orders import (
    CreateOrderRequest, UpdateStatusRequest,
    OrderResponse, PaginatedOrdersResponse, StatusHistoryEntry,
)
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=PaginatedOrdersResponse)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: sqlite3.Connection = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return order_service.get_orders(
        db, page=page, page_size=page_size,
        status=status, search=search,
        date_from=date_from, date_to=date_to,
    )


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    body: CreateOrderRequest,
    db: sqlite3.Connection = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return order_service.create_order(db, body.customer_name, body.customer_email, body.total_amount)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: sqlite3.Connection = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return order_service.get_order(db, order_id)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def update_status(
    order_id: int,
    body: UpdateStatusRequest,
    db: sqlite3.Connection = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return order_service.update_status(db, order_id, body.status)


@router.get("/{order_id}/history", response_model=list[StatusHistoryEntry])
def get_history(
    order_id: int,
    db: sqlite3.Connection = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    return order_service.get_history(db, order_id)
