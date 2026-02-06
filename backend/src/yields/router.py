from datetime import date

from fastapi import APIRouter, Depends

from src.yields.dependencies import get_yield_date
from src.yields.schemas import YieldCurveResponse
from src.yields import service as yields_service

router = APIRouter(prefix="/api/yields", tags=["Yields"])


@router.get(
    "",
    response_model=YieldCurveResponse,
    summary="Get yield curve",
    description="Returns treasury yield curve data. Currently returns fake data regardless of the date parameter.",
)
async def get_yields(
    _date: date | None = Depends(get_yield_date),
) -> YieldCurveResponse:
    """Return yield curve (fake data; date ignored)."""
    return yields_service.get_fake_yield_curve()
