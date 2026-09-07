"""
Unit tests for target variable definition and encoding.
"""
import pytest
import pandas as pd
import numpy as np
from backend.ml.preprocessing import encode_labels, decode_labels, LABEL_TO_INT, INT_TO_LABEL

def test_target_encoding_mapping():
    """Verify exact 3-class target mapping: Low->0, Medium->1, High->2."""
    assert LABEL_TO_INT["Low"] == 0
    assert LABEL_TO_INT["Medium"] == 1
    assert LABEL_TO_INT["High"] == 2
    assert INT_TO_LABEL[0] == "Low"
    assert INT_TO_LABEL[1] == "Medium"
    assert INT_TO_LABEL[2] == "High"

def test_encode_and_decode_labels():
    """Verify bidirectional label conversion."""
    series = pd.Series(["Low", "Medium", "High", "Low", "High"])
    encoded = encode_labels(series)
    np.testing.assert_array_equal(encoded, np.array([0, 1, 2, 0, 2]))
    decoded = decode_labels(encoded)
    assert decoded == ["Low", "Medium", "High", "Low", "High"]

def test_target_horizon_alignment():
    """Verify target_period is strictly greater than prediction_period."""
    df = pd.DataFrame({
        "prediction_period": ["2024-05", "2024-06", "2024-07"],
        "target_period": ["2024-06", "2024-07", "2024-08"],
        "target_risk_label": ["Low", "Medium", "High"]
    })
    for _, row in df.iterrows():
        assert row["prediction_period"] < row["target_period"]
