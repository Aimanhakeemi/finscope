from app.main import app
from fastapi.testclient import TestClient


def test_healthz_returns_documented_body():
    with TestClient(app) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0", "llm_enabled": False}


def test_healthz_rejects_wrong_method():
    with TestClient(app) as client:
        response = client.post("/healthz")
    assert response.status_code == 405
