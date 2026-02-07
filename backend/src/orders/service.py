"""Order business logic."""

from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.orders.models import Order
from src.orders.schemas import OrderCreate, OrderUpdate, OrderResponse
from src.yields import service as yields_service


async def list_orders(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 10,
) -> tuple[list[OrderResponse], int]:
    """Return orders newest first with pagination; returns (orders, total)."""
    count_result = await db.execute(select(func.count()).select_from(Order))
    total = count_result.scalar() or 0
    result = await db.execute(
        select(Order).order_by(Order.created_at.desc()).offset(offset).limit(limit)
    )
    orders = result.scalars().all()
    return [_order_to_response(o) for o in orders], total


async def create_order(db: AsyncSession, body: OrderCreate) -> OrderResponse:
    """Create an order: resolve today's yield for the term, persist with status Pending."""
    curve = await yields_service.get_yield_curve(date.today())
    point = next((p for p in curve.data if p.term == body.term), None)
    if point is None:
        raise HTTPException(
            status_code=404,
            detail=f"No yield for term {body.term} for today",
        )
    order = Order(
        date=date.today(),
        term=body.term,
        amount=body.amount,
        yield_pct=point.rate,
        status="Pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return _order_to_response(order)


async def update_order_status(db: AsyncSession, order_id: int, body: OrderUpdate) -> OrderResponse:
    """Update order status; only Pending -> Settled or Pending -> Failed allowed."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail=f"Only Pending orders can be updated; current status is {order.status}",
        )
    if body.status not in ("Settled", "Failed"):
        raise HTTPException(
            status_code=400,
            detail="Status must be Settled or Failed",
        )
    order.status = body.status
    await db.commit()
    await db.refresh(order)
    return _order_to_response(order)


def _order_to_response(order: Order) -> OrderResponse:
    """Map Order model to OrderResponse."""
    return OrderResponse(
        id=order.id,
        date=order.date.isoformat(),
        term=order.term,
        amount=float(order.amount),
        yield_pct=order.yield_pct,
        status=order.status,
        created_at=order.created_at.isoformat(),
    )
