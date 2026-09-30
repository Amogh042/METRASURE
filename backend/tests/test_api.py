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

def _admin_headers():
    token = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_calculate_stores_band_rule_per_result():
    headers = _admin_headers()
    inst = next(i for i in client.get("/api/instruments/", headers=headers).json() if i["instrument_id"] == "DEMO-001")
    test_id = client.post("/api/tests/", json={"instrument_id": inst["id"], "test_type": "Full Calibration"}, headers=headers).json()["id"]
    for seq, load in enumerate([5.00, 5.01, 20.01], start=1):
        client.post(f"/api/tests/{test_id}/measurements", json={"test_module": "Accuracy", "sequence": seq, "test_load": load, "indicated_value": load, "unit": "kg"}, headers=headers)

    res = client.post(f"/api/tests/{test_id}/calculate", params={"test_module": "Accuracy"}, headers=headers)
    assert res.status_code == 200
    assert [m["rule_id"] for m in res.json()["calculated_values"]["measurements"]] == ["R76-ACC-III-001", "R76-ACC-III-002", "R76-ACC-III-003"]

    rule_codes = {r["id"]: r["rule_id"] for r in client.get("/api/rules/", headers=headers).json()}
    results = client.get(f"/api/tests/{test_id}/results", headers=headers).json()
    assert sorted(rule_codes[r["rule_id"]] for r in results) == ["R76-ACC-III-001", "R76-ACC-III-002", "R76-ACC-III-003"]

def test_calculate_load_above_class_range_returns_400():
    headers = _admin_headers()
    inst = next(i for i in client.get("/api/instruments/", headers=headers).json() if i["instrument_id"] == "DEMO-001")
    test_id = client.post("/api/tests/", json={"instrument_id": inst["id"], "test_type": "Full Calibration"}, headers=headers).json()["id"]
    client.post(f"/api/tests/{test_id}/measurements", json={"test_module": "Accuracy", "sequence": 1, "test_load": 100.01, "indicated_value": 100.01, "unit": "kg"}, headers=headers)

    res = client.post(f"/api/tests/{test_id}/calculate", params={"test_module": "Accuracy"}, headers=headers)
    assert res.status_code == 400
    assert "outside every configured MPE band" in res.json()["detail"]

def test_rule_with_invalid_condition_is_rejected():
    headers = _admin_headers()
    res = client.post("/api/rules/", headers=headers, json={
        "rule_id": "R76-TEST-BAD", "standard": "OIML R-76-1", "standard_version": "2006", "test_type": "Accuracy",
        "accuracy_class": "III", "condition": "m > 500e; drop", "formula_reference": "1e", "permissible_error": 1.0,
        "unit": "e", "reason": "test"
    })
    assert res.status_code == 400
