"""
Unit tests for feature definitions and derived feature engineering.
"""
import pytest
import pandas as pd
import numpy as np
from backend.ml.features import (
    TRANSACTION_FEATURES,
    RECONCILIATION_FEATURES,
    COMPLIANCE_FEATURES,
    ITC_FEATURES,
    ALL_TABULAR_FEATURES,
    engineer_derived_features,
    get_feature_group_columns
)

def test_feature_groups_non_empty():
    """Verify primary feature groups contain valid expected columns."""
    assert len(TRANSACTION_FEATURES) >= 4
    assert len(RECONCILIATION_FEATURES) >= 4
    assert len(COMPLIANCE_FEATURES) >= 4
    assert len(ITC_FEATURES) >= 1
    assert "invoice_count" in TRANSACTION_FEATURES
    assert "mismatch_rate" in RECONCILIATION_FEATURES
    assert "missing_gstr3b_count" in COMPLIANCE_FEATURES
    assert "itc_exposure" in ITC_FEATURES

def test_derived_features_engineering():
    """Verify derived features are calculated cleanly without division by zero or NaN."""
    df = pd.DataFrame({
        "invoice_count": [0, 5, 10],
        "total_invoice_value": [0.0, 50000.0, 100000.0],
        "total_tax": [0.0, 9000.0, 18000.0],
        "itc_exposure": [0.0, 4500.0, 25000.0],
        "missing_gstr1_count": [0, 1, 0],
        "missing_gstr3b_count": [0, 1, 1],
        "mismatch_rate": [0.0, 0.4, 0.8],
        "duplicate_invoice_count": [0, 1, 0]
    })
    
    engineered = engineer_derived_features(df)
    
    assert "itc_exposure_ratio" in engineered.columns
    assert "tax_per_invoice" in engineered.columns
    assert "unfiled_return_ratio" in engineered.columns
    assert "mismatch_severity_index" in engineered.columns
    
    # Assert zero NaNs
    for col in ["itc_exposure_ratio", "tax_per_invoice", "unfiled_return_ratio", "mismatch_severity_index"]:
        assert engineered[col].isna().sum() == 0
        assert (engineered[col] >= 0.0).all()

def test_get_feature_group_columns():
    """Verify retrieval of feature subsets for ablation."""
    tx_cols = get_feature_group_columns("transaction")
    assert tx_cols == TRANSACTION_FEATURES
    
    tx_rec_cols = get_feature_group_columns("transaction_reconciliation")
    assert len(tx_rec_cols) == len(TRANSACTION_FEATURES) + len(RECONCILIATION_FEATURES)
