# Treasury Dashboard

A full-stack application for bank liquidity and treasury management. It pulls treasury yield data, visualizes the yield curve, and supports order submission (by term and amount) with a view of historical orders.

The interface is **professional and fintech-focused**: it prioritizes clarity, scannability of data, and immediate feedback for user actions (e.g., clear error messages when something goes wrong).

## Tech Stack

| Layer       | Technology                          |
|------------|--------------------------------------|
| **Backend** | Python 3.11+, FastAPI               |
| **Database** | PostgreSQL                          |
| **ORM**     | SQLAlchemy 2.0 (Alembic for migrations) |
| **Validation** | Pydantic v2                      |
| **Frontend** | React, Vite, Tailwind CSS          |

## Getting Started

### Prerequisites

- **Node.js** (LTS) and npm
- **Python 3.11+**

### Backend

From the project root:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn src.main:app --reload
```

API runs at `http://localhost:8000`. OpenAPI docs: `http://localhost:8000/docs`.

### Frontend

From the project root (in a separate terminal):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The **Treasury Yields** page is the default view: it shows a yield curve chart and a date selector. The backend currently returns fake data regardless of the selected date.

### References

- [FastAPI best practices](https://github.com/zhanymkanov/fastapi-best-practices) — Backend structure, async routes, dependency injection, and Pydantic conventions used in this project.
