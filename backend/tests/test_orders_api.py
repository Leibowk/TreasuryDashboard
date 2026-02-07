"""API tests for orders: GET /api/orders, POST /api/order, PATCH /api/orders/{id}."""

from datetime import date
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from sqlalchemy import text

from src.db import engine
from src.yields.schemas import YieldCurveResponse, YieldPoint


def _clear_orders():
    """Delete all orders so tests start from a clean state."""
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM orders"))
        conn.commit()


def test_get_orders_empty_200(client):
    """GET /api/orders returns 200 with empty list when no orders."""
    _clear_orders()
    response = client.get("/api/orders")
    assert response.status_code == 200
    assert response.json() == {"orders": [], "total": 0}


def test_post_order_201_and_list(client):
    """POST /api/order creates order; GET /api/orders returns it."""
    _clear_orders()
    mock_curve = YieldCurveResponse(
        data=[
            YieldPoint(term="1M", rate=4.35),
            YieldPoint(term="5Y", rate=4.24),
            YieldPoint(term="10Y", rate=4.43),
        ],
        display_date=date.today().isoformat(),
    )
    with patch(
        "src.orders.service.yields_service.get_yield_curve",
        new_callable=AsyncMock,
        return_value=mock_curve,
    ):
        response = client.post(
            "/api/order",
            json={"term": "5Y", "amount": 10_000},
        )
    assert response.status_code == 201
    body = response.json()
    assert body["term"] == "5Y"
    assert body["amount"] == 10_000
    assert body["yield_pct"] == 4.24
    assert body["status"] == "Pending"
    assert "id" in body
    assert "date" in body
    assert "created_at" in body

    list_resp = client.get("/api/orders")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    orders = data["orders"]
    assert len(orders) == 1
    assert orders[0]["id"] == body["id"]
    assert orders[0]["status"] == "Pending"


def test_post_order_invalid_term_422(client):
    """POST /api/order with invalid term returns 422."""
    _clear_orders()
    response = client.post(
        "/api/order",
        json={"term": "99Y", "amount": 1000},
    )
    assert response.status_code == 422


def test_post_order_no_yield_404(client):
    """POST /api/order returns 404 when no yield for today for that term."""
    _clear_orders()
    mock_curve = YieldCurveResponse(
        data=[
            YieldPoint(term="1M", rate=4.35),
        ],
        display_date=date.today().isoformat(),
    )
    with patch(
        "src.orders.service.yields_service.get_yield_curve",
        new_callable=AsyncMock,
        return_value=mock_curve,
    ):
        response = client.post(
            "/api/order",
            json={"term": "5Y", "amount": 1000},
        )
    assert response.status_code == 404
    assert "5Y" in response.json().get("detail", "")


def test_patch_order_settled_200(client):
    """PATCH /api/orders/{id} to Settled returns 200 and updates order."""
    _clear_orders()
    mock_curve = YieldCurveResponse(
        data=[YieldPoint(term="10Y", rate=4.43)],
        display_date=date.today().isoformat(),
    )
    with patch(
        "src.orders.service.yields_service.get_yield_curve",
        new_callable=AsyncMock,
        return_value=mock_curve,
    ):
        create_resp = client.post("/api/order", json={"term": "10Y", "amount": 5000})
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/api/orders/{order_id}", json={"status": "Settled"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "Settled"

    list_resp = client.get("/api/orders")
    assert list_resp.json()["orders"][0]["status"] == "Settled"


def test_patch_order_failed_200(client):
    """PATCH /api/orders/{id} to Failed returns 200."""
    _clear_orders()
    mock_curve = YieldCurveResponse(
        data=[YieldPoint(term="2Y", rate=4.17)],
        display_date=date.today().isoformat(),
    )
    with patch(
        "src.orders.service.yields_service.get_yield_curve",
        new_callable=AsyncMock,
        return_value=mock_curve,
    ):
        create_resp = client.post("/api/order", json={"term": "2Y", "amount": 1000})
    assert create_resp.status_code == 201
    order_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/api/orders/{order_id}", json={"status": "Failed"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "Failed"


def test_patch_order_not_found_404(client):
    """PATCH /api/orders/99999 returns 404."""
    _clear_orders()
    response = client.patch("/api/orders/99999", json={"status": "Settled"})
    assert response.status_code == 404


def test_patch_order_invalid_transition_400(client):
    """PATCH to change a non-Pending order returns 400."""
    _clear_orders()
    mock_curve = YieldCurveResponse(
        data=[YieldPoint(term="5Y", rate=4.24)],
        display_date=date.today().isoformat(),
    )
    with patch(
        "src.orders.service.yields_service.get_yield_curve",
        new_callable=AsyncMock,
        return_value=mock_curve,
    ):
        create_resp = client.post("/api/order", json={"term": "5Y", "amount": 1000})
    order_id = create_resp.json()["id"]
    client.patch(f"/api/orders/{order_id}", json={"status": "Settled"})

    # Now try to change again
    response = client.patch(f"/api/orders/{order_id}", json={"status": "Failed"})
    assert response.status_code == 400
    assert "Pending" in response.json().get("detail", "")
