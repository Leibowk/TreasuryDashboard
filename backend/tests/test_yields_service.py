"""Unit tests for yields.service."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from src.yields.schemas import TERM_LABELS, YieldCurveResponse
from src.yields import service as yields_service


@patch("src.yields.service._is_before_release_cst")
@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_success(mock_date_module, mock_fetch, mock_before_release):
    """get_yield_curve returns YieldCurveResponse for requested date (today when None)."""
    yields_service._fallback_cache = None
    mock_before_release.return_value = False
    today = date(2025, 2, 5)
    mock_date_module.today.return_value = today
    mock_fetch.return_value = [{"date": "2025-02-05", "value": "4.35"}]

    result = await yields_service.get_yield_curve(None)

    assert isinstance(result, YieldCurveResponse)
    assert len(result.data) == 8
    assert [p.term for p in result.data] == list(TERM_LABELS)
    assert all(p.rate == 4.35 for p in result.data)
    assert result.display_date == "2025-02-05"


@patch("src.yields.service._fallback_start_date")
@patch("src.yields.service._is_before_release_cst")
@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_skips_missing_value(
    mock_date_module, mock_fetch, mock_before_release, mock_fallback_start
):
    """get_yield_curve returns 404 when target date has no valid data and fallback finds none."""
    yields_service._fallback_cache = None
    mock_before_release.return_value = False
    mock_fallback_start.return_value = date(2025, 2, 5)
    mock_date_module.today.return_value = date(2025, 2, 5)
    mock_fetch.return_value = [{"date": "2025-02-05", "value": "."}]

    with pytest.raises(HTTPException) as exc_info:
        await yields_service.get_yield_curve(None)

    assert exc_info.value.status_code == 404


@patch("src.yields.service._fallback_start_date")
@patch("src.yields.service._is_before_release_cst")
@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_404_when_no_data(
    mock_date_module, mock_fetch, mock_before_release, mock_fallback_start
):
    """get_yield_curve raises 404 when target date has no data and fallback finds none."""
    yields_service._fallback_cache = None
    mock_before_release.return_value = False
    mock_fallback_start.return_value = date(2025, 2, 5)
    mock_date_module.today.return_value = date(2025, 2, 5)
    mock_fetch.return_value = []

    with pytest.raises(HTTPException) as exc_info:
        await yields_service.get_yield_curve(None)

    assert exc_info.value.status_code == 404
    assert "No FRED data" in exc_info.value.detail


@patch("src.yields.service._fallback_start_date")
@patch("src.yields.service._is_before_release_cst")
@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_fallback_to_yesterday(
    mock_date_module, mock_fetch, mock_before_release, mock_fallback_start
):
    """When target date (today) has no data, get_yield_curve returns fallback (yesterday)."""
    yields_service._fallback_cache = None
    mock_before_release.return_value = False
    today = date(2025, 2, 7)
    yesterday = date(2025, 2, 6)
    mock_date_module.today.return_value = today
    mock_fallback_start.return_value = yesterday
    mock_fetch.side_effect = lambda series_id, obs_date: (
        [] if obs_date == today else [{"date": "2025-02-06", "value": "4.42"}]
    )

    result = await yields_service.get_yield_curve(None)

    assert result.display_date == "2025-02-06"
    assert len(result.data) == 8
    assert all(p.rate == 4.42 for p in result.data)


@patch("src.yields.service._is_before_release_cst")
@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_default_date(mock_date_module, mock_fetch, mock_before_release):
    """get_yield_curve with None uses today as date_to_try and returns its data."""
    yields_service._fallback_cache = None
    mock_before_release.return_value = False
    today = date(2025, 2, 6)
    mock_date_module.today.return_value = today
    mock_fetch.return_value = [{"date": "2025-02-06", "value": "4.40"}]

    result = await yields_service.get_yield_curve(None)

    assert result.display_date == "2025-02-06"
    mock_fetch.assert_called()
    call_args = mock_fetch.call_args_list[0]
    assert call_args[0][1] == today  # second positional arg is obs_date


@patch("src.yields.service._fallback_start_date")
@patch("src.yields.service.fred_service.fetch_observations")
@patch("src.yields.service.date")
async def test_get_yield_curve_future_date_returns_fallback(
    mock_date_module, mock_fetch, mock_fallback_start
):
    """When target_date is in the future, return fallback data; do not query FRED for that date."""
    yields_service._fallback_cache = None
    today = date(2025, 2, 5)
    future_date = date(2025, 2, 10)
    mock_date_module.today.return_value = today
    mock_fallback_start.return_value = today  # fallback computation starts from today
    mock_fetch.return_value = [{"date": "2025-02-05", "value": "4.35"}]

    result = await yields_service.get_yield_curve(future_date)

    assert result.display_date == "2025-02-05"
    assert len(result.data) == 8
    # FRED must never be called with the future date
    for call in mock_fetch.call_args_list:
        obs_date = call[0][1]
        assert obs_date <= today, "FRED was called with a future date"
