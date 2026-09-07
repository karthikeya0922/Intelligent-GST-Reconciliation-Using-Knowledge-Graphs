"""
Unit tests for RiskExplanationGenerator.
Verifies class-specific SHAP factor attribution, narrative generation, and disclaimers.
"""

import pytest
from backend.ml.explanation import RiskExplanationGenerator


def test_narrative_explanation_generation_and_disclaimer():
    """Verifies generated explanation contains mandatory score, factors, and disclaimer."""
    gen = RiskExplanationGenerator()

    top_factors = [
        {"feature": "average_filing_delay", "shap_value": 0.45, "impact": "high"},
        {"feature": "mismatch_severity_index", "shap_value": 0.32, "impact": "high"},
        {"feature": "late_filing_count", "shap_value": 0.18, "impact": "medium"}
    ]

    narrative = gen.generate_explanation(
        vendor_id="V1023",
        prediction_period="2026-03",
        model_class="HIGH",
        risk_score=82.4,
        risk_band="HIGH",
        itc_exposure=125000.0,
        itc_exposure_ratio=0.31,
        top_factors=top_factors,
        priority="CRITICAL",
        recommended_action="Priority audit and Rule 36(4) ITC blockage review"
    )

    # Verifications
    assert "V1023" in narrative
    assert "HIGH" in narrative
    assert "82.4" in narrative
    assert "125,000.00" in narrative
    assert "31.0%" in narrative
    assert "statutory return filing delay" in narrative
    assert "CRITICAL" in narrative
    # Statutory disclaimer verification
    assert "Disclaimer:" in narrative
    assert "does not constitute an official statutory GST tax assessment" in narrative
    assert "decision support" in narrative
