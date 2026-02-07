"""Pytest fixtures for Treasury Dashboard backend tests."""

import os

# Must set before any app imports (Settings loads these at import time)
os.environ.setdefault("APP_FRED_API_KEY", "test_key")
# Use a file DB so all connections share the same DB (in-memory would create a new DB per connection)
os.environ.setdefault("APP_DATABASE_URL", "sqlite:///./test_treasury.db")

import pytest
from starlette.testclient import TestClient

from src.db import Base, engine
from src.main import app

# Ensure tables exist before any test runs (TestClient may not run lifespan in time)
Base.metadata.create_all(bind=engine)

# Sample FRED observations for reuse in tests
mock_fred_observations = [{"date": "2025-02-05", "value": "4.43"}]


def pytest_configure():
    """Ensure APP_FRED_API_KEY is set before any app code runs."""
    os.environ.setdefault("APP_FRED_API_KEY", "test_key")


@pytest.fixture
def client() -> TestClient:
    """Return a test client for the FastAPI app."""
    return TestClient(app)
