from typing import List
from pydantic import BaseModel


class OrderTrendPoint(BaseModel):
    date: str
    all: int
    pending: int
    paid: int
    shipped: int
    cancelled: int


class TopCustomer(BaseModel):
    name: str
    email: str
    orders: int
    total: float


class ReportsSummary(BaseModel):
    trend: List[OrderTrendPoint]
    topCustomers: List[TopCustomer]
    avgFulfillmentDays: float
    cancellationRate: int
    revenueThisMonth: float
    revenuePrevMonth: float
    peakDay: str
    peakDayCount: int
