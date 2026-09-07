"""
Phase 4 End-to-End API Integration & Regression Tests.

Tests:
1. /risk/summary dynamic calculation
2. /risk/vendors paginated listing
3. Vendor search (by id, name, gstin, state)
4. Risk class filtering (LOW, MEDIUM, HIGH)
5. Operational priority filtering (LOW, MEDIUM, HIGH, CRITICAL)
6. Risk score sorting (asc, desc)
7. ITC exposure sorting (asc, desc)
8. Pagination metadata and offset logic
9. /risk/vendor/{id}/graph endpoint
10. Graph temporal cutoff enforcement (t <= requested_period)
11. Graph depth parameter validation (depth 1 and 2, reject > 2)
12. Nonexistent vendor -> 404
13. Invalid period format -> 400
14. Invalid pagination parameters -> 422
15. Model Class and Operational Priority conceptual separation
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend"))
from backend.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_1_risk_summary_dynamic_calculation(client):
    """1. /risk/summary returns dynamic calculated metrics from actual dataset."""
    resp = client.get("/risk/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_vendors"] == 2015
    assert "risk_distribution" in data
    assert data["risk_distribution"]["LOW"] > 0
    assert data["risk_distribution"]["MEDIUM"] > 0
    assert data["risk_distribution"]["HIGH"] > 0
    assert sum(data["risk_distribution"].values()) == 2015

    assert "total_itc_exposure" in data
    assert data["total_itc_exposure"] > 0.0

    assert "exposure_by_risk_class" in data
    assert "LOW" in data["exposure_by_risk_class"]
    assert "HIGH" in data["exposure_by_risk_class"]

    assert "risk_exposure_matrix" in data
    assert len(data["risk_exposure_matrix"]) == 6

    assert "operational_priority_distribution" in data
    assert "CRITICAL" in data["operational_priority_distribution"]

    assert "exposure_over_time" in data
    assert len(data["exposure_over_time"]) >= 20


def test_2_risk_vendors_endpoint(client):
    """2. /risk/vendors returns paginated vendor items with correct structure."""
    resp = client.get("/risk/vendors?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert len(data["items"]) == 10
    assert "pagination" in data
    assert data["pagination"]["total_records"] == 2015
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 10
    assert data["pagination"]["total_pages"] == 202

    v0 = data["items"][0]
    assert "vendor_id" in v0
    assert "vendor_name" in v0
    assert "risk_score" in v0
    assert "itc_exposure" in v0
    assert "priority" in v0
    assert "trend" in v0


def test_3_vendor_search(client):
    """3. Vendor search works across vendor_id and vendor_name."""
    resp = client.get("/risk/vendors?search=V0001")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    assert any(item["vendor_id"] == "V0001" for item in data["items"])


def test_4_risk_filter(client):
    """4. Risk filter correctly limits to specified class."""
    resp = client.get("/risk/vendors?risk_class=HIGH&page_size=20")
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["model_class"] == "HIGH" or item["risk_band"] == "HIGH"


def test_5_priority_filter(client):
    """5. Priority filter correctly limits to specified operational priority."""
    resp = client.get("/risk/vendors?priority=CRITICAL&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total_records"] > 0
    for item in data["items"]:
        assert item["priority"] == "CRITICAL"


def test_6_score_sorting(client):
    """6. Score sorting correctly orders descending and ascending."""
    resp_desc = client.get("/risk/vendors?sort=risk_score&order=desc&page_size=10")
    assert resp_desc.status_code == 200
    scores_desc = [item["risk_score"] for item in resp_desc.json()["items"]]
    assert scores_desc == sorted(scores_desc, reverse=True)

    resp_asc = client.get("/risk/vendors?sort=risk_score&order=asc&page_size=10")
    assert resp_asc.status_code == 200
    scores_asc = [item["risk_score"] for item in resp_asc.json()["items"]]
    assert scores_asc == sorted(scores_asc)


def test_7_exposure_sorting(client):
    """7. Exposure sorting correctly orders descending."""
    resp = client.get("/risk/vendors?sort=itc_exposure&order=desc&page_size=10")
    assert resp.status_code == 200
    exposures = [item["itc_exposure"] for item in resp.json()["items"]]
    assert exposures == sorted(exposures, reverse=True)


def test_8_pagination(client):
    """8. Pagination correctly offsets across pages."""
    resp_p1 = client.get("/risk/vendors?page=1&page_size=5&sort=vendor_id&order=asc")
    resp_p2 = client.get("/risk/vendors?page=2&page_size=5&sort=vendor_id&order=asc")
    vids_p1 = [i["vendor_id"] for i in resp_p1.json()["items"]]
    vids_p2 = [i["vendor_id"] for i in resp_p2.json()["items"]]

    assert len(vids_p1) == 5
    assert len(vids_p2) == 5
    assert len(set(vids_p1).intersection(set(vids_p2))) == 0


def test_9_graph_endpoint(client):
    """9. /risk/vendor/{vendor_id}/graph returns nodes, edges, and metadata."""
    resp = client.get("/risk/vendor/V0001/graph?period=2026-02&depth=1")
    assert resp.status_code == 200
    data = resp.json()

    assert "nodes" in data
    assert "edges" in data
    assert "metadata" in data
    assert data["metadata"]["center_vendor"] == "V0001"
    assert data["metadata"]["depth"] == 1
    assert any(n["is_target"] for n in data["nodes"])


def test_10_graph_temporal_cutoff(client):
    """10. Graph temporal cutoff excludes any relationships after requested period."""
    # Simulation started in 2024-04; a cutoff before that must have zero edges
    resp_pre = client.get("/risk/vendor/V0001/graph?period=2023-12&depth=1")
    assert resp_pre.status_code == 200
    data_pre = resp_pre.json()
    assert len(data_pre["edges"]) == 0

    # A cutoff in 2026-02 includes valid benchmark relationships
    resp_post = client.get("/risk/vendor/V0001/graph?period=2026-02&depth=1")
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert len(data_post["edges"]) > 0


def test_11_graph_depth_limitation(client):
    """11. Graph depth is restricted to 1 and 2; larger depths are rejected with 422."""
    resp_d1 = client.get("/risk/vendor/V0001/graph?depth=1")
    assert resp_d1.status_code == 200

    resp_d2 = client.get("/risk/vendor/V0001/graph?depth=2")
    assert resp_d2.status_code == 200
    assert len(resp_d2.json()["nodes"]) >= len(resp_d1.json()["nodes"])

    # Depth 3 is rejected
    resp_d3 = client.get("/risk/vendor/V0001/graph?depth=3")
    assert resp_d3.status_code == 422


def test_12_nonexistent_vendor_404(client):
    """12. Requesting a nonexistent vendor returns 404."""
    resp = client.get("/risk/vendor/NONEXISTENT_VENDOR_99999")
    assert resp.status_code == 404

    resp_graph = client.get("/risk/vendor/NONEXISTENT_VENDOR_99999/graph")
    assert resp_graph.status_code == 404

    resp_hist = client.get("/risk/vendor/NONEXISTENT_VENDOR_99999/history")
    assert resp_hist.status_code == 404


def test_13_invalid_period_400(client):
    """13. Invalid period format returns 400 Bad Request."""
    resp_summary = client.get("/risk/summary?period=invalid-period")
    assert resp_summary.status_code == 400

    resp_vendors = client.get("/risk/vendors?period=2025/08")
    assert resp_vendors.status_code == 400

    resp_graph = client.get("/risk/vendor/V0001/graph?period=not-a-period")
    assert resp_graph.status_code == 400


def test_14_invalid_pagination_422(client):
    """14. Invalid pagination parameters return 422 Unprocessable Entity."""
    resp_p0 = client.get("/risk/vendors?page=0")
    assert resp_p0.status_code == 422

    resp_sz0 = client.get("/risk/vendors?page_size=0")
    assert resp_sz0.status_code == 422

    resp_sz_huge = client.get("/risk/vendors?page_size=500")
    assert resp_sz_huge.status_code == 422


def test_15_model_class_operational_priority_separation(client):
    """15. Model Class (LOW/MED/HIGH) and Operational Priority (LOW/MED/HIGH/CRITICAL) remain distinct."""
    # Summary verification
    summary_resp = client.get("/risk/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    model_classes = set(summary["risk_distribution"].keys())
    operational_priorities = set(summary["operational_priority_distribution"].keys())

    assert model_classes == {"LOW", "MEDIUM", "HIGH"}
    assert "CRITICAL" in operational_priorities
    assert "CRITICAL" not in model_classes

    # Vendor level separation: LOW risk class with high exposure gets MEDIUM priority
    low_resp = client.get("/risk/vendors?risk_class=LOW&page_size=50")
    assert low_resp.status_code == 200
    low_items = low_resp.json()["items"]
    assert all(i["model_class"] == "LOW" for i in low_items)
    # Priorities for LOW risk class can be LOW or MEDIUM (never CRITICAL)
    low_item_priorities = set(i["priority"] for i in low_items)
    assert "LOW" in low_item_priorities
    assert "CRITICAL" not in low_item_priorities

    # HIGH risk class with high exposure gets CRITICAL priority
    crit_resp = client.get("/risk/vendors?priority=CRITICAL&page_size=10")
    assert crit_resp.status_code == 200
    crit_items = crit_resp.json()["items"]
    assert len(crit_items) > 0
    assert all(i["priority"] == "CRITICAL" for i in crit_items)
    assert all(i["model_class"] == "HIGH" for i in crit_items)
