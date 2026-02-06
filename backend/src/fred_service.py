"""FRED API client for fetching Treasury yield observations."""

from datetime import date

import httpx

from src.config import settings


async def fetch_observations(series_id: str, obs_date: date) -> list[dict]:
    """
    Fetch observations for a FRED series for the given date.

    Args:
        series_id: FRED series ID (e.g. DGS1MO, DGS10).
        obs_date: Date for which to fetch observations.

    Returns:
        List of observation dicts with 'date' and 'value' keys.

    Raises:
        httpx.HTTPStatusError: On HTTP errors from FRED API.
        ValueError: On invalid or unexpected response format.
    """
    date_str = obs_date.isoformat()
    url = (
        f"{settings.FRED_BASE_URL}/fred/series/observations"
        f"?series_id={series_id}"
        f"&api_key={settings.FRED_API_KEY}"
        f"&file_type=json"
        f"&observation_start={date_str}"
        f"&observation_end={date_str}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
    data = response.json()
    if "observations" not in data:
        raise ValueError(f"Invalid FRED response: missing 'observations'")
    return data["observations"]
