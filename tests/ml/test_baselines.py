"""
Unit tests for Majority and Rule-Based Baseline models.
"""
import pytest
import pandas as pd
import numpy as np
from backend.ml.baselines import MajorityBaseline, RuleBasedBaseline

def test_majority_baseline():
    """Verify MajorityBaseline predicts class 0 and returns deterministic probabilities."""
    clf = MajorityBaseline(majority_class=0)
    df = pd.DataFrame({"dummy": [1, 2, 3, 4]})
    preds = clf.predict(df)
    probas = clf.predict_proba(df)
    
    assert (preds == 0).all()
    assert probas.shape == (4, 3)
    np.testing.assert_allclose(probas[:, 0], 1.0)
    np.testing.assert_allclose(probas[:, 1:], 0.0)

def test_rule_based_baseline_thresholds():
    """Verify RuleBasedBaseline applies documented experimental thresholds (<0.20, 0.20-0.50, >=0.50)."""
    clf = RuleBasedBaseline()
    
    # 1. Clean compliant row -> score < 0.20 -> class 0 (Low)
    row_low = pd.DataFrame([{
        "missing_gstr3b_count": 0,
        "missing_gstr1_count": 0,
        "mismatch_rate": 0.05,
        "average_filing_delay": 0.0,
        "duplicate_invoice_count": 0
    }])
    
    # 2. Moderate discrepancy -> score in [0.20, 0.50) -> class 1 (Medium)
    row_med = pd.DataFrame([{
        "missing_gstr3b_count": 0,
        "missing_gstr1_count": 1,  # +0.25 penalty
        "mismatch_rate": 0.10,
        "average_filing_delay": 2.0,
        "duplicate_invoice_count": 0
    }])
    
    # 3. Severe non-compliance -> score >= 0.50 -> class 2 (High)
    row_high = pd.DataFrame([{
        "missing_gstr3b_count": 1,  # +0.35 penalty
        "missing_gstr1_count": 1,  # +0.25 penalty
        "mismatch_rate": 0.80,
        "average_filing_delay": 25.0,
        "duplicate_invoice_count": 1
    }])
    
    pred_low = clf.predict(row_low)[0]
    pred_med = clf.predict(row_med)[0]
    pred_high = clf.predict(row_high)[0]
    
    assert pred_low == 0, f"Expected Low (0), got {pred_low}"
    assert pred_med == 1, f"Expected Medium (1), got {pred_med}"
    assert pred_high == 2, f"Expected High (2), got {pred_high}"
    
    # Check probabilities sum to 1.0
    for row in [row_low, row_med, row_high]:
        probs = clf.predict_proba(row)[0]
        assert abs(probs.sum() - 1.0) < 1e-5
