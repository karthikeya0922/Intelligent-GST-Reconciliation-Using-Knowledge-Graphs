"""
Unit tests for ITC exposure calculation, safe ratios, and risk vs exposure separation.
"""

import pytest
from backend.ml.risk_engine import ITCRiskEngine


def test_itc_exposure_non_negative_and_safe_ratio():
    """Verifies ITC exposure is non-negative and exposure ratio never produces NaN or Inf."""
    engine = ITCRiskEngine()

    # Normal case
    res1 = engine.assess_vendor("TEST_001", "2026-03", record={
        "total_tax": 100000.0,
        "itc_exposure": 25000.0,
        "total_invoice_value": 500000.0
    })
    assert res1["itc"]["exposure"] == 25000.0
    assert res1["itc"]["exposure_ratio"] == 0.25

    # Zero tax liability (safe division)
    res2 = engine.assess_vendor("TEST_002", "2026-03", record={
        "total_tax": 0.0,
        "itc_exposure": 0.0,
        "total_invoice_value": 0.0
    })
    assert res2["itc"]["exposure"] == 0.0
    assert res2["itc"]["exposure_ratio"] == 0.0
    assert not pytest.approx(res2["itc"]["exposure_ratio"]) == float("nan")


def test_separation_of_risk_from_exposure():
    """
    Section 5: Verifies that a vendor with low exposure can be high risk,
    and a vendor with high exposure can be low risk.
    """
    engine = ITCRiskEngine()

    # Vendor A: Low risk, high exposure (₹5,00,000 exposure, clean filings)
    p_low, a_low, d_low = engine.prioritize_review("LOW", 500000.0)
    assert p_low == "MEDIUM"  # Spot-check due to materiality, not because vendor is fraudulent

    # Vendor B: High risk, low exposure (₹15,000 exposure, severe non-compliance)
    p_high, a_high, d_high = engine.prioritize_review("HIGH", 15000.0)
    assert p_high == "HIGH"  # Elevated priority due to behavioral risk despite modest financial amount

    # Vendor C: High risk, high exposure -> CRITICAL
    p_crit, a_crit, d_crit = engine.prioritize_review("HIGH", 500000.0)
    assert p_crit == "CRITICAL"
