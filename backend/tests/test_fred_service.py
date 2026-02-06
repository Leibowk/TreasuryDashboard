"""Unit tests for fred_service."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.fred_service import fetch_observations


@pytest.fixture
def mock_observations():
    return [{"date": "2025-02-05", "value": "4.43"}]


@patch("src.fred_service.httpx.AsyncClient")
async def test_fetch_observations_success(mock_client_class, mock_observations):
    """Fetch observations returns observations list on success."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"observations": mock_observations}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    result = await fetch_observations("DGS10", date(2025, 2, 5))
    assert result == mock_observations


@patch("src.fred_service.httpx.AsyncClient")
async def test_fetch_observations_invalid_response(mock_client_class):
    """Fetch observations raises ValueError when response lacks observations."""
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    with pytest.raises(ValueError, match="missing 'observations'"):
        await fetch_observations("DGS10", date(2025, 2, 5))


@patch("src.fred_service.httpx.AsyncClient")
async def test_fetch_observations_http_error_propagates(mock_client_class):
    """Fetch observations propagates httpx.HTTPStatusError on HTTP errors."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client

    with pytest.raises(httpx.HTTPStatusError):
        await fetch_observations("DGS10", date(2025, 2, 5))
