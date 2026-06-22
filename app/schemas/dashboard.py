from typing import Dict, List
from pydantic import BaseModel


class OrdersPerDay(BaseModel):
    date: str
    count: int


class DashboardSummary(BaseModel):
    total_orders: int
    orders_by_status: Dict[str, int]
    total_revenue: float
    avg_order_value: float
    orders_today: int
    orders_per_day: List[OrdersPerDay]
