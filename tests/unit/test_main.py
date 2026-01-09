import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root():
    """Test the root endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "Agent Backend",
        "version": "1.0.0"
    }


@pytest.mark.asyncio
async def test_health():
    """Test the health check endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "connected",
        "service": "Agent Backend"
    }
