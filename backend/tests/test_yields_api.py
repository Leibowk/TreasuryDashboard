"""API tests for GET /api/yields."""

from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from src.yields.schemas import YieldCurveResponse, YieldPoint


async def test_get_yields_200_with_date(client):
    """GET /api/yields?date=2025-02-05 returns 200 with yield data."""
    mock_response = YieldCurveResponse(
        data=[
            YieldPoint(term="1M", rate=4.35),
            YieldPoint(term="3M", rate=4.33),
            YieldPoint(term="6M", rate=4.27),
            YieldPoint(term="1Y", rate=4.17),
            YieldPoint(term="2Y", rate=4.17),
            YieldPoint(term="5Y", rate=4.24),
            YieldPoint(term="10Y", rate=4.43),
            YieldPoint(term="30Y", rate=4.64),
        ],
        display_date="2025-02-05",
    )

    with patch(
        "src.yields.router.yields_service.get_yield_curve",
        new_callable=AsyncMock,
        return_value=mock_response,
    ) as mock_get:
        response = await client.get("/api/yields?date=2025-02-05")

    assert response.status_code == 200
    json = response.json()
    assert "data" in json
    assert len(json["data"]) == 8
    assert json["data"][0]["term"] == "1M"
    assert json["data"][0]["rate"] == 4.35
    assert json["display_date"] == "2025-02-05"
    mock_get.assert_called_once()


async def test_get_yields_200_without_date(client):
    """GET /api/yields returns 200 when no date param (defaults to today)."""
    mock_response = YieldCurveResponse(
        data=[YieldPoint(term=t, rate=4.0) for t in ("1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "30Y")],
        display_date="2025-02-06",
    )

    with patch(
        "src.yields.router.yields_service.get_yield_curve",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        response = await client.get("/api/yields")

    assert response.status_code == 200
    json = response.json()
    assert len(json["data"]) == 8


async def test_get_yields_404_when_no_data(client):
    """GET /api/yields returns 404 when no FRED data for date."""
    with patch(
        "src.yields.router.yields_service.get_yield_curve",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=404, detail="No FRED data for date"),
    ):
        response = await client.get("/api/yields?date=2025-02-05")

    assert response.status_code == 404
    assert "No FRED data" in response.json().get("detail", "")
