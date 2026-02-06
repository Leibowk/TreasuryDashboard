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
    description="Returns treasury yield curve data from FRED for the given date.",
)
async def get_yields(
    _date: date | None = Depends(get_yield_date),
) -> YieldCurveResponse:
    """Return yield curve from FRED for the requested date."""
    return await yields_service.get_yield_curve(_date)
