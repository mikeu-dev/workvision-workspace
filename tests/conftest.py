"""
Pytest Global Configuration & Fixtures.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from workvision_api.main import app
from workvision_config import Settings, get_settings


@pytest.fixture
def settings() -> Settings:
    """Fixture providing cached application settings."""
    return get_settings()


@pytest.fixture
async def async_api_client():
    """Async HTTP Client for testing FastAPI endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client
