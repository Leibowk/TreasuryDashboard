import asyncio
from datetime import date, timedelta

from fastapi import HTTPException

from src.config import TERM_TO_SERIES_ID
from src import fred_service
from src.yields.schemas import TERM_LABELS, YieldPoint, YieldCurveResponse


async def _fetch_curve_for_date(obs_date: date) -> list[YieldPoint] | None:
    """Fetch yield curve for a single date. Returns None if no data."""

    async def fetch_for_term(term: str, series_id: str) -> YieldPoint | None:
        observations = await fred_service.fetch_observations(series_id, obs_date)
        for obs in observations:
            val = obs.get("value")
            if val and val != ".":
                try:
                    rate = float(val)
                    if rate >= 0:
                        return YieldPoint(term=term, rate=rate)
                except (TypeError, ValueError):
                    continue
        return None

    tasks = [
        fetch_for_term(term, series_id)
        for term, series_id in TERM_TO_SERIES_ID.items()
    ]
    results = await asyncio.gather(*tasks)
    data = [p for p in results if p is not None]
    if not data:
        return None

    term_order = {t: i for i, t in enumerate(TERM_LABELS)}
    data.sort(key=lambda p: term_order.get(p.term, len(term_order)))
    return data


async def get_yield_curve(target_date: date | None = None) -> YieldCurveResponse:
    """
    Fetch real yield curve data from FRED for the given date.
    If no data for the requested date, retries with yesterday's date.

    Args:
        target_date: Date for yield data; defaults to today if None.

    Returns:
        YieldCurveResponse with term/rate points and display_date.

    Raises:
        HTTPException: 404 if no FRED data for requested date or yesterday.
    """
    obs_date = target_date or date.today()

    data = await _fetch_curve_for_date(obs_date)
    if data is not None:
        return YieldCurveResponse(data=data, display_date=obs_date.isoformat())

    # Retry with yesterday's date
    fallback_date = obs_date - timedelta(days=1)
    data = await _fetch_curve_for_date(fallback_date)
    if data is not None:
        return YieldCurveResponse(data=data, display_date=fallback_date.isoformat())

    raise HTTPException(
        status_code=404,
        detail=f"No FRED data for date {obs_date.isoformat()} or {fallback_date.isoformat()}",
    )
