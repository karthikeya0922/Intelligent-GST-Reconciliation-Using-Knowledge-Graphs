"""
Unit tests for data preprocessing and transformation pipelines.
"""
import pytest
import pandas as pd
import numpy as np
from backend.ml.preprocessing import build_preprocessor

def test_preprocessor_fitting_and_transformation():
    """Verify preprocessor fits on train and transforms validation without schema drift."""
    features = ["invoice_count", "total_invoice_value", "mismatch_rate"]
    train_data = pd.DataFrame({
        "invoice_count": [2, 5, 8],
        "total_invoice_value": [10000.0, 50000.0, 80000.0],
        "mismatch_rate": [0.0, 0.2, 0.5]
    })
    test_data = pd.DataFrame({
        "invoice_count": [3, np.nan],  # Missing value in test
        "total_invoice_value": [30000.0, 60000.0],
        "mismatch_rate": [0.1, 0.3]
    })

    preprocessor = build_preprocessor(features, scale_features=True)
    preprocessor.fit(train_data[features])

    X_train = preprocessor.transform(train_data[features])
    X_test = preprocessor.transform(test_data[features])

    assert X_train.shape == (3, 3)
    assert X_test.shape == (2, 3)
    # Check that missing value in test_data was imputed with median
    assert not np.isnan(X_test).any()

def test_unscaled_preprocessor():
    """Verify unscaled preprocessor preserves native values (for tree models)."""
    features = ["invoice_count", "mismatch_rate"]
    df = pd.DataFrame({
        "invoice_count": [10, 20],
        "mismatch_rate": [0.25, 0.75]
    })
    prep = build_preprocessor(features, scale_features=False)
    prep.fit(df)
    X = prep.transform(df)
    np.testing.assert_allclose(X[0], [10.0, 0.25])
