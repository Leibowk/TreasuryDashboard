import asyncio
from datetime import date, timedelta

import httpx
from fastapi import HTTPException

from src.config import TERM_TO_SERIES_ID
from src import fred_service
from src.yields.schemas import TERM_LABELS, YieldPoint, YieldCurveResponse


async def _fetch_curve_for_date(obs_date: date) -> list[YieldPoint] | None:
    """Fetch yield curve for a single date. Returns None if no data."""

    async def fetch_for_term(term: str, series_id: str) -> YieldPoint | None:
        try:
            observations = await fred_service.fetch_observations(series_id, obs_date)
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            raise HTTPException(
                status_code=504,
                detail="FRED API timed out. Please try again.",
            ) from e
        except httpx.ConnectError as e:
            raise HTTPException(
                status_code=503,
                detail="FRED API is temporarily unavailable. Please try again later.",
            ) from e
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
    Fetch treasury yield curve from FRED. Always uses calendar today and
    yesterday only: tries today first, then yesterday, and returns whichever
    date has data. The date query param is accepted for API compatibility but
    does not change which dates are fetched.

    Returns:
        YieldCurveResponse with term/rate points and display_date (today or yesterday).

    Raises:
        HTTPException: 404 if no FRED data for today or yesterday.
    """
    data = await _fetch_curve_for_date(target_date)
    if data is not None:
        return YieldCurveResponse(data=data, display_date=target_date.isoformat())

    today = date.today()
    yesterday = today - timedelta(days=1)

    # Always try today first, then yesterday
    data = await _fetch_curve_for_date(today)
    if data is not None:
        return YieldCurveResponse(data=data, display_date=today.isoformat())

    data = await _fetch_curve_for_date(yesterday)
    if data is not None:
        return YieldCurveResponse(data=data, display_date=yesterday.isoformat())

    raise HTTPException(
        status_code=404,
        detail=f"No FRED data for today ({today.isoformat()}) or yesterday ({yesterday.isoformat()})",
    )
