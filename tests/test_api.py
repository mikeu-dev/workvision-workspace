"""
Integration Tests for FastAPI Backend (workvision-api).
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check_endpoint(async_api_client: AsyncClient):
    """Test /health endpoint returns 200 OK and valid health payload."""
    response = await async_api_client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "workvision-api"
    assert data["app_name"] == "WorkVision AI"
    assert "environment" in data
    assert "version" in data
