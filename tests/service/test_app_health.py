import pytest
import asyncio
from config import app

@pytest.mark.asyncio
async def test_health_endpoint():
    test_client = app.test_client()
    resp = await test_client.get('/health')
    assert resp.status_code == 200
    data = await resp.get_json()
    assert data["status"] == "ok"
    # depending on bot init race, application_running may be True/False but should be present
    assert "application_running" in data["details"] 