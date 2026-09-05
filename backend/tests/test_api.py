import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200

# Basic endpoints test
def test_get_instruments():
    # Attempting to fetch instruments. Need auth token or mock.
    # Since endpoints are protected, we can test auth first.
    response = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    token = response.json().get("access_token")
    
    headers = {"Authorization": f"Bearer {token}"}
    inst_response = client.get("/api/instruments/", headers=headers)
    assert inst_response.status_code == 200
    assert len(inst_response.json()) >= 1
