import asyncio
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException

from src.config import TERM_TO_SERIES_ID
from src import fred_service
from src.yields.schemas import TERM_LABELS, YieldPoint, YieldCurveResponse

# Economic data is released daily around 4:15 PM CST (America/Chicago).
RELEASE_TIME_CST = time(16, 15)
CST = ZoneInfo("America/Chicago")

# Fallback: last weekday with economic data. TTL 30 minutes.
_FALLBACK_TTL_SECONDS = 30 * 60
_fallback_cache: dict | None = None


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


async def _fetch_curve_for_date_safe(obs_date: date) -> list[YieldPoint] | None:
    """Like _fetch_curve_for_date but returns None on any failure (for fallback computation)."""
    try:
        return await _fetch_curve_for_date(obs_date)
    except HTTPException:
        return None


def _fallback_cache_valid() -> bool:
    """True if cached fallback exists and is within TTL."""
    global _fallback_cache
    if _fallback_cache is None:
        return False
    computed_at = _fallback_cache.get("computed_at")
    if computed_at is None:
        return False
    elapsed = (datetime.now(timezone.utc) - computed_at).total_seconds()
    return elapsed < _FALLBACK_TTL_SECONDS


def _is_before_release_cst() -> bool:
    """True if current time is before 4:15 PM CST (data not yet released for today)."""
    now_cst = datetime.now(CST)
    return now_cst.time() < RELEASE_TIME_CST


def _previous_weekday(d: date) -> date:
    """Go back one calendar day, then skip over weekends (Sat/Sun)."""
    d = d - timedelta(days=1)
    while d.weekday() >= 5:  # 5=Saturday, 6=Sunday
        d = d - timedelta(days=1)
    return d


def _fallback_start_date() -> date:
    """
    First date to try when computing fallback (weekday only).
    Before 4:15 PM CST: don't query today; start from previous weekday (e.g. Friday if Monday).
    After 4:15 PM CST: start from today if weekday, else previous weekday.
    """
    now_cst = datetime.now(CST)
    today_cst = now_cst.date()
    if _is_before_release_cst():
        # No data for today yet; start from yesterday (or last weekday)
        d = today_cst - timedelta(days=1)
    else:
        d = today_cst
    while d.weekday() >= 5:
        d = d - timedelta(days=1)
    return d


async def _compute_fallback_response() -> YieldCurveResponse:
    """
    Walk backwards by weekday only from start_date until we find a day with FRED data.
    Start_date skips today if before 4:15 PM CST. Caches result with TTL.
    """
    global _fallback_cache
    d = _fallback_start_date()
    max_weekdays = 30
    while max_weekdays > 0:
        data = await _fetch_curve_for_date_safe(d)
        if data is not None:
            response = YieldCurveResponse(data=data, display_date=d.isoformat())
            _fallback_cache = {
                "response": response,
                "computed_at": datetime.now(timezone.utc),
            }
            return response
        d = _previous_weekday(d)
        max_weekdays -= 1
    raise HTTPException(
        status_code=404,
        detail="No FRED data found in the last 30 weekdays.",
    )

async def _get_fallback_response() -> YieldCurveResponse:
    """Return cached fallback if TTL valid; otherwise recompute and return."""
    if _fallback_cache_valid():
        return _fallback_cache["response"]
    return await _compute_fallback_response()


async def get_yield_curve(target_date: date | None = None) -> YieldCurveResponse:
    """
    Fetch treasury yield curve. Returns target_date's data when available; otherwise fallback.
    Future dates or today-before-release (before 4:15 PM CST) return fallback without querying.
    """
    today = date.today()
    date_to_try = target_date if target_date is not None else today

    if (target_date is not None and target_date > today) or (date_to_try == today and _is_before_release_cst()):
        return await _get_fallback_response()

    data = await _fetch_curve_for_date(date_to_try)
    if data is not None:
        return YieldCurveResponse(data=data, display_date=date_to_try.isoformat())

    return await _get_fallback_response()
