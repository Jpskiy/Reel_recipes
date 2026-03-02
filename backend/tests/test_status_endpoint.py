from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_status_endpoint_shape_not_found():
    response = client.get("/api/recipes/does-not-exist/status")
    assert response.status_code == 404
    assert "detail" in response.json()
