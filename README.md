# Treasury Dashboard

A full-stack application for bank liquidity and treasury management. It pulls treasury yield data, visualizes the yield curve, and supports order submission (by term and amount) with a view of historical orders.

The interface is **professional and fintech-focused**: it prioritizes clarity, scannability of data, and immediate feedback for user actions (e.g., clear error messages when something goes wrong).

## Tech Stack

| Layer       | Technology                          |
|------------|--------------------------------------|
| **Backend** | Python 3.11+, FastAPI               |
| **Database** | SQLite (default);                  |
| **ORM**     | SQLAlchemy 2.0 (Alembic for migrations) | 
| **Validation** | Pydantic v2                      |
| **Frontend** | React, Vite, Tailwind CSS          |

## Getting Started

### Prerequisites

- **Node.js** (LTS) and npm
- **Python 3.11+**

### Environment variables

You must provide a `.env` file in the `backend` directory or set the required environment variables before running the backend. Copy `backend/.env.example` to `backend/.env` and fill in the values, or get the variable values from another developer on the project.

Required:

- `APP_FRED_API_KEY` — API key for the FRED (Federal Reserve Economic Data) API; required for yield curve data.

- `APP_DATABASE_URL` — Database URL (default: `sqlite:///./treasury.db`). Set to a PostgreSQL URL if you prefer.

Optional:
- `APP_CORS_ORIGINS` — Allowed CORS origins (default includes `http://localhost:5173`).

### Backend

From the project root:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
# Optional: run migrations (tables are also created on startup)
alembic upgrade head
uvicorn src.main:app --reload
```

API runs at `http://localhost:8000`. OpenAPI docs: `http://localhost:8000/docs`. Orders (create order, order history) require the backend and database to be running; the app uses SQLite by default (file `treasury.db` in the backend directory). To use PostgreSQL, set `APP_DATABASE_URL` in `.env` (see `backend/.env.example`).

### Frontend

From the project root (in a separate terminal):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The **Treasury Yields** page is the default view: it shows a yield curve chart and a date selector. Below that, **Order History** lists all orders and **Create Order** lets you submit an order for a term and amount (today’s yield is fetched from the backend). Pending orders can be set to Settled or Failed. The backend returns real yield data from FRED for the selected date.

### Running Tests

**Backend** (from project root):

```bash
cd backend
pytest tests/ -v
```

Tests mock the FRED API; a real API key is not needed for assertions. `APP_FRED_API_KEY` is still required at import time because the app loads it from the environment. Order API tests use a temporary SQLite file (`test_treasury.db`); no separate database setup is required.

**Frontend** (from project root):

```bash
cd frontend
npm run test
```

Runs Vitest with React Testing Library; API tests mock `fetch` for `api/yields` and `api/orders`. Use `npm run test:run` for a single run (CI).

## Architecture

- **Frontend** (React + Vite) calls the backend REST API for yield curve data and orders.
- **Backend** (FastAPI) exposes `/api/yields` and `/api/orders` (and `/api/order` for create). It uses **SQLAlchemy** (async) for persistence and the **FRED API** for treasury rates.
- **Yields**: The backend fetches series from FRED, maps terms to series IDs, and caches a **fallback date** (last weekday with data, 30‑min TTL) used when the requested date has no data or for future dates.
- **Orders:** In a production flow, order submissions would be forwarded to an external execution/clearing API and settlement system. For this take-home we intentionally "fake" execution: orders are created and stored locally with status `Pending`, and the frontend can update them to `Settled` or `Failed`. We do, however, resolve and store the trade yield using the FRED API for the order date (or the cache's last-available date / fallback) so the `yield_pct` on each order reflects real market rates — see the cache behavior above. The creation logic is implemented in the order service: [backend/src/orders/service.py](backend/src/orders/service.py).
- **Order status (Settled / Failed):** In a real flow, status changes would typically be driven by a clearing house or settlement system and then reflected via APIs. Here we simulate that with a **button on the frontend** that calls `PATCH /api/orders/{id}` to update status. This keeps the UI simple and demonstrates the transition (Pending → Settled or Failed) without integrating with an external clearing house.

## Design decisions

- **Economic data cache:** The backend caches the last weekday with FRED data (30 min TTL). That fallback is used when the requested date has no data, for future dates, and when “today” is before 4:15 PM CST (data not yet released). Weekday-only walkback and skipping “today” before release reduce FRED calls and match release semantics.
- **Single global config:** FRED, CORS, DB, and term-to-series mapping live in one config module for simplicity; config can be split by domain later if the app grows.
- **Async backend, async test client:** The app uses async route handlers and an async DB session. Tests use `httpx.AsyncClient` with `ASGITransport` so the test client runs on the same event loop as the app.
- **Orders:** A single service layer with an injected async session; no Repository or Unit of Work. This is intentional for the current single-entity scope; a Repository could be added if the domain grows.


### TODO

- **Add authentication** — Protect API and UI with login/session or API keys as appropriate for the environment.
- **Adjust caching as necessary** — The backend uses a **fallback date** (last weekday with FRED data, 30 min TTL) when the requested date has no data. For orders and historical views, consider a more specific rule (e.g. previous Friday for weekends, or a proper business-day calendar).
- **Optional:** Split config by domain (e.g. yields vs orders) if the app grows.
- **Optional:** Hide OpenAPI docs in production (`openapi_url=None`).
- **Optional:** Extract domain exceptions (e.g. `OrderNotFound`, `InvalidOrderState`) for clearer error handling.

### References

- [FastAPI best practices](https://github.com/zhanymkanov/fastapi-best-practices) — Backend structure, async routes, dependency injection, and Pydantic conventions used in this project.
