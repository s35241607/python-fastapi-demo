import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def client():
    """同步測試客戶端"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """非同步測試客戶端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
