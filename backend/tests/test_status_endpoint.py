from fastapi.testclient import TestClient

from app.config import settings


def test_status_endpoint_shape(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path / "storage"))
    from app import main as app_main

    monkeypatch.setattr(app_main, "_run_pipeline", lambda recipe_id, recipe_storage: None)
    client = TestClient(app_main.app)
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
