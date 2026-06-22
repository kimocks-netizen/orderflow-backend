from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class CreateOrderRequest(BaseModel):
    customer_name: str = Field(min_length=1)
    customer_email: EmailStr
    total_amount: float = Field(ge=0)


class UpdateStatusRequest(BaseModel):
    status: str


class StatusHistoryEntry(BaseModel):
    id: int
    order_id: int
    from_status: Optional[str]
    to_status: str
    changed_at: str


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    total_amount: float
    status: str
    created_at: str
    updated_at: str


class PaginatedOrdersResponse(BaseModel):
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
