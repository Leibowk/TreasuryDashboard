"""Pytest fixtures for Treasury Dashboard backend tests."""

import os

# Must set before any app imports (Settings loads FRED_API_KEY at import time)
os.environ.setdefault("APP_FRED_API_KEY", "test_key")

import pytest
from starlette.testclient import TestClient

from src.main import app

# Sample FRED observations for reuse in tests
mock_fred_observations = [{"date": "2025-02-05", "value": "4.43"}]


def pytest_configure():
    """Ensure APP_FRED_API_KEY is set before any app code runs."""
    os.environ.setdefault("APP_FRED_API_KEY", "test_key")


@pytest.fixture
def client() -> TestClient:
    """Return a test client for the FastAPI app."""
    return TestClient(app)
