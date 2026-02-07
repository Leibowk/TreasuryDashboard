"""Unit tests for yields.service."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from src.yields.schemas import TERM_LABELS, YieldCurveResponse
from src.yields import service as yields_service


@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_success(mock_date_module, mock_fetch):
    """get_yield_curve returns YieldCurveResponse for today (today then yesterday)."""
    today = date(2025, 2, 5)
    mock_date_module.today.return_value = today
    mock_fetch.return_value = [{"date": "2025-02-05", "value": "4.35"}]

    result = await yields_service.get_yield_curve(None)

    assert isinstance(result, YieldCurveResponse)
    assert len(result.data) == 8
    assert [p.term for p in result.data] == list(TERM_LABELS)
    assert all(p.rate == 4.35 for p in result.data)
    assert result.display_date == "2025-02-05"


@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_skips_missing_value(mock_date_module, mock_fetch):
    """get_yield_curve skips terms with '.' value; raises 404 when no valid data for today or yesterday."""
    mock_date_module.today.return_value = date(2025, 2, 5)
    mock_fetch.return_value = [{"date": "2025-02-05", "value": "."}]

    with pytest.raises(HTTPException) as exc_info:
        await yields_service.get_yield_curve(None)

    assert exc_info.value.status_code == 404


@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_404_when_no_data(mock_date_module, mock_fetch):
    """get_yield_curve raises HTTPException 404 when no data for today or yesterday."""
    mock_date_module.today.return_value = date(2025, 2, 5)
    mock_fetch.return_value = []

    with pytest.raises(HTTPException) as exc_info:
        await yields_service.get_yield_curve(None)

    assert exc_info.value.status_code == 404
    assert "No FRED data" in exc_info.value.detail
    assert "today" in exc_info.value.detail.lower() and "yesterday" in exc_info.value.detail.lower()


@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_fallback_to_yesterday(mock_date_module, mock_fetch):
    """When today has no data, get_yield_curve returns yesterday's data."""
    today = date(2025, 2, 7)
    yesterday = date(2025, 2, 6)
    mock_date_module.today.return_value = today
    # Today returns no observations; yesterday returns data
    mock_fetch.side_effect = lambda series_id, obs_date: (
        [] if obs_date == today else [{"date": "2025-02-06", "value": "4.42"}]
    )

    result = await yields_service.get_yield_curve(None)

    assert result.display_date == "2025-02-06"
    assert len(result.data) == 8
    assert all(p.rate == 4.42 for p in result.data)


@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_default_date(mock_date_module, mock_fetch):
    """get_yield_curve tries today first, then yesterday; returns first with data."""
    today = date(2025, 2, 6)
    mock_date_module.today.return_value = today
    mock_fetch.return_value = [{"date": "2025-02-06", "value": "4.40"}]

    result = await yields_service.get_yield_curve(None)

    assert result.display_date == "2025-02-06"
    mock_fetch.assert_called()
    # First fetch is for today
    call_args = mock_fetch.call_args_list[0]
    assert call_args[0][1] == today  # second positional arg is obs_date
