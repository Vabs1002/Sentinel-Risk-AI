import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"

def test_risk_scoring_endpoint(client):
    payload = {
        "order_id": "ORD-API-TEST",
        "order_amount": 3499.0,
        "is_cod": 1,
        "pincode_historical_rto": 0.28,
        "device_order_count_24h": 1
    }
    response = client.post("/api/v1/risk/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "decision" in data
    assert "latency_ms" in data

def test_syndicates_endpoint(client):
    response = client.get("/api/v1/graph/syndicates")
    assert response.status_code == 200
    data = response.json()
    assert "total_syndicates_detected" in data
