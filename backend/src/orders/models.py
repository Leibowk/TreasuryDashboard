"""SQLAlchemy model for orders."""

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, Integer, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Order(Base):
    """Order for a specific term and amount, with yield at order time."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    term: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    yield_pct: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_now)
