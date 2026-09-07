"""
Unit tests for the production prediction interface and schema.
"""
import pytest
from backend.ml.predict import GSTVendorRiskPredictor

def test_prediction_output_schema():
    """Verify predict output conforms strictly to application API expectations."""
    predictor = GSTVendorRiskPredictor(models_dir="non_existent_dir")
    
    record = {
        "mismatch_rate": 0.05,
        "average_filing_delay": 0.0,
        "invoice_count": 5
    }
    result = predictor.predict(vendor_id="V001", period="2026-03", record=record)
    
    assert "vendor_id" in result
    assert "period" in result
    assert "risk_class" in result
    assert "risk_probability" in result
    assert "top_factors" in result
    
    assert result["risk_class"] in ["LOW", "MEDIUM", "HIGH"]
    probs = result["risk_probability"]
    assert "LOW" in probs
    assert "MEDIUM" in probs
    assert "HIGH" in probs
    
    # Assert probability sum equals 1.0 (within numerical tolerance)
    prob_sum = probs["LOW"] + probs["MEDIUM"] + probs["HIGH"]
    assert abs(prob_sum - 1.0) < 1e-4

def test_high_risk_prediction_factors():
    """Verify high discrepancy records generate high-risk indicators and factors."""
    predictor = GSTVendorRiskPredictor(models_dir="non_existent_dir")
    record = {
        "mismatch_rate": 0.85,
        "average_filing_delay": 20.0,
        "invoice_count": 10
    }
    result = predictor.predict(vendor_id="V_RISKY", period="2026-03", record=record)
    assert result["risk_class"] == "HIGH"
    assert len(result["top_factors"]) > 0
