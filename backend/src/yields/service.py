from src.yields.schemas import TERM_LABELS, YieldPoint, YieldCurveResponse


def get_fake_yield_curve() -> YieldCurveResponse:
    """
    Return a plausible upward-sloping fake yield curve.
    Date is ignored for this ticket; same curve is always returned.
    """
    # Plausible rates in percent (upward slope)
    rates = (5.32, 5.28, 5.24, 5.18, 5.02, 4.88, 4.72, 4.65)
    data = [YieldPoint(term=t, rate=r) for t, r in zip(TERM_LABELS, rates)]
    return YieldCurveResponse(data=data)
