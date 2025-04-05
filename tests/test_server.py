from fastapi.testclient import TestClient
from spiderfs_mcp.server import app


client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}