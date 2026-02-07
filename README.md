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

From the project root:

```bash
cd backend
pytest tests/ -v
```

Tests mock the FRED API; a real API key is not needed for assertions. `APP_FRED_API_KEY` is still required at import time because the app loads it from the environment. Order API tests use a temporary SQLite file (`test_treasury.db`); no separate database setup is required.

### TODO

- **Add authentication** — Protect API and UI with login/session or API keys as appropriate for the environment.
- **Adjust caching as necessary** — The backend computes a **fallback date** (the last calendar day with economic data from FRED), caches it with a 30-minute TTL, and uses that when there is no data for the requested date (e.g. future dates) or when today/yesterday have no data. For **orders** and for **past economic data** (e.g. past weekends or holidays), a more specific rule may be better—for example, use the **previous Friday** when the requested date falls on a weekend, or a proper business-day calendar. The current “last day with data” approach is generic; consider aligning with how orders and historical views should reference “as of” dates.

### References

- [FastAPI best practices](https://github.com/zhanymkanov/fastapi-best-practices) — Backend structure, async routes, dependency injection, and Pydantic conventions used in this project.
