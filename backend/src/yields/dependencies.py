from datetime import date

from fastapi import Query


async def get_yield_date(
    date_param: date | None = Query(None, alias="date", description="Date for yield curve (ignored for fake data)")
) -> date | None:
    """Dependency to parse and return optional date query param."""
    return date_param
