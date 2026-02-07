"""Orders API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import get_db
from src.orders.schemas import OrderCreate, OrderListResponse, OrderResponse, OrderUpdate
from src.orders import service as orders_service
from src.yields.schemas import TERM_LABELS

router = APIRouter(prefix="/api", tags=["Orders"])


@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="List orders",
    description="Returns all orders, newest first.",
)
async def get_orders(db: AsyncSession = Depends(get_db)) -> OrderListResponse:
    """Return all orders."""
    orders = await orders_service.list_orders(db)
    return OrderListResponse(orders=orders)


@router.post(
    "/order",
    response_model=OrderResponse,
    status_code=201,
    summary="Create order",
    description="Create an order for the given term and amount; uses today's yield for that term.",
)
async def post_order(
    body: OrderCreate,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """Create an order (term, amount); yield is fetched for today."""
    if body.term not in TERM_LABELS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid term; must be one of: {', '.join(TERM_LABELS)}",
        )
    return await orders_service.create_order(db, body)


@router.patch(
    "/orders/{order_id}",
    response_model=OrderResponse,
    summary="Update order status",
    description="Update a Pending order to Settled or Failed.",
)
async def patch_order(
    order_id: int,
    body: OrderUpdate,
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """Update order status (Settled or Failed)."""
    return await orders_service.update_order_status(db, order_id, body)
