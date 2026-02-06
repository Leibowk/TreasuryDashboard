from pydantic import BaseModel, Field

# Standard treasury curve terms (display order)
TERM_LABELS = ("1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "30Y")


class YieldPoint(BaseModel):
    """Single point on the yield curve."""

    term: str = Field(..., description="Term label (e.g. 1M, 3M, 1Y, 30Y)")
    rate: float = Field(..., description="Yield rate in percent", ge=0)


class YieldCurveResponse(BaseModel):
    """Response for the yield curve endpoint."""

    data: list[YieldPoint] = Field(..., description="Ordered list of term/rate points")
    display_date: str = Field(
        ...,
        description="Date the data is from (YYYY-MM-DD); may differ from requested date when data not yet released",
    )
