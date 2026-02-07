"""Pydantic schemas for orders API."""

from datetime import date, datetime

from pydantic import BaseModel, Field

ORDER_STATUSES = ("Pending", "Settled", "Failed")


class OrderCreate(BaseModel):
    """Request body for creating an order."""

    term: str = Field(..., description="Term label (e.g. 5Y, 10Y)")
    amount: float = Field(..., gt=0, description="Order amount in dollars")


class OrderUpdate(BaseModel):
    """Request body for updating order status."""

    status: str = Field(..., description="New status: Settled or Failed")


class OrderResponse(BaseModel):
    """Order as returned by the API."""

    id: int
    date: str
    term: str
    amount: float
    yield_pct: float
    status: str
    created_at: str

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """Response for GET /api/orders (paginated)."""

    orders: list[OrderResponse]
    total: int = Field(..., description="Total number of orders")
