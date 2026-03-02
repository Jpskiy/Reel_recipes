from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_status_endpoint_shape():
    upload = client.post(
        "/api/recipes/upload",
        files={"file": ("sample.mp4", b"fake-video-bytes", "video/mp4")},
    )
    assert upload.status_code == 200
    recipe_id = upload.json()["id"]

    status_res = client.get(f"/api/recipes/{recipe_id}/status")
    assert status_res.status_code == 200
    data = status_res.json()

    assert set(data.keys()) == {"status", "progress", "error"}
    assert isinstance(data["progress"], int)
