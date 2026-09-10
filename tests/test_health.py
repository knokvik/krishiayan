from fastapi.testclient import TestClient

from krishiayan.api.main import app

client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "Krishiayan"


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "docs" in r.json()
