from datetime import date

from fastapi import Query


async def get_yield_date(
    date_param: date | None = Query(None, alias="date", description="Date for yield curve; defaults to today if omitted")
) -> date:
    """Dependency that provides the date query param (alias 'date'); returns today when omitted."""
    return date_param if date_param is not None else date.today()
