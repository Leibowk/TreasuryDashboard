"""Pytest fixtures for Treasury Dashboard backend tests."""

import os

# Must set before any app imports (Settings loads these at import time)
os.environ.setdefault("APP_FRED_API_KEY", "test_key")
# Use a file DB so all connections share the same DB (in-memory would create a new DB per connection)
os.environ.setdefault("APP_DATABASE_URL", "sqlite:///./test_treasury.db")

import pytest
from httpx import ASGITransport, AsyncClient

from src.db import Base, engine
from src.main import app

# Ensure tables exist before any test runs
Base.metadata.create_all(bind=engine)

# Sample FRED observations for reuse in tests
mock_fred_observations = [{"date": "2025-02-05", "value": "4.43"}]


def pytest_configure(config):
    """Ensure APP_FRED_API_KEY is set and enable pytest-asyncio auto mode."""
    os.environ.setdefault("APP_FRED_API_KEY", "test_key")
    config.addinivalue_line("markers", "asyncio: mark test as async (pytest-asyncio)")


@pytest.fixture
async def client():
    """Return an async test client for the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
