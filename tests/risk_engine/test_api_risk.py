"""
Integration tests for production Risk API endpoints.
Verifies response schemas, status codes, and backward compatibility.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure backend package is in python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend"))
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_post_risk_predict_endpoint(client):
    """Verifies POST /risk/predict returns 200 and conforms to production schema."""
    resp = client.post("/risk/predict", json={
        "vendor_id": "V001",
        "period": "2026-03"
    })
    assert resp.status_code == 200
    data = resp.json()

    # Schema checks
    assert data["vendor_id"] == "V001"
    assert "risk" in data
    assert "model_class" in data["risk"]
    assert "risk_band" in data["risk"]
    assert "score" in data["risk"]
    assert "probabilities" in data["risk"]
    assert "LOW" in data["risk"]["probabilities"]

    assert "itc" in data
    assert "exposure" in data["itc"]
    assert "exposure_ratio" in data["itc"]

    assert "evidence" in data
    assert "reconciliation" in data["evidence"]
    assert "compliance" in data["evidence"]

    assert "recommendations" in data
    assert "review_priority" in data["recommendations"]

    assert "explanation_text" in data
    # Backward compatibility aliases
    assert "risk_class" in data
    assert "risk_score" in data


def test_get_vendor_risk_endpoint(client):
    """Verifies GET /risk/vendor/{vendor_id} returns 200."""
    resp = client.get("/risk/vendor/V001?period=2026-03")
    assert resp.status_code == 200
    data = resp.json()
    assert data["vendor_id"] == "V001"
    assert "risk" in data


def test_get_vendor_history_endpoint(client):
    """Verifies GET /risk/vendor/{vendor_id}/history returns 200 with history and trend."""
    resp = client.get("/risk/vendor/V001/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["vendor_id"] == "V001"
    assert "trend" in data
    assert "transitions" in data
    assert "history" in data
    assert isinstance(data["history"], list)
