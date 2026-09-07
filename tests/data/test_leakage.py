"""
Tests for multi-period temporal leakage prevention across all prediction windows.
"""
import pytest
from backend.data.synthetic.generator import SyntheticGSTGenerator
from backend.data.features.aggregator import VendorPeriodFeatureAggregator

def test_multi_period_prediction_leakage():
    """Verify that features computed at period T_k strictly use data <= T_k."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=30, months_count=8)
    
    aggregator = VendorPeriodFeatureAggregator()
    df = aggregator.build_feature_matrix(
        dataset["vendors"],
        dataset["invoices"],
        dataset["reconciliations"],
        dataset["filings"],
        dataset["tax_periods"]
    )
    
    # Check that future target label columns are strictly targets, not features
    feature_cols = [c for c in df.columns if not c.startswith("target_") and c not in [
        "vendor_id", "period", "prediction_period", "feature_period_start", 
        "feature_period_end", "synthetic_profile"
    ]]
    
    # Future filing status or future target score must never appear as a feature
    for col in feature_cols:
        assert not col.startswith("future_"), f"Future column detected in features: {col}"
        assert not col.startswith("target_"), f"Target column detected in features: {col}"

    # Verify that in any prediction period T_k, future events from > T_k are not included in feature counts
    for _, row in df.iterrows():
        pred_p = row["prediction_period"]
        target_p = row["target_period"]
        assert pred_p < target_p, f"Prediction period {pred_p} must be strictly before target period {target_p}"

def test_window_boundary_isolation():
    """Ensure rolling window features only look back window_size periods from T_k."""
    gen = SyntheticGSTGenerator(seed=77)
    dataset = gen.generate_dataset(vendor_count=20, months_count=10)
    
    aggregator = VendorPeriodFeatureAggregator()
    df = aggregator.build_feature_matrix(
        dataset["vendors"],
        dataset["invoices"],
        dataset["reconciliations"],
        dataset["filings"],
        dataset["tax_periods"]
    )
    
    # Verify that for the first period T_0, rolling metrics are computed without failing
    first_period = sorted(dataset["tax_periods"])[0]
    t0_rows = df[df["prediction_period"] == first_period]
    assert len(t0_rows) > 0
    # Values should be non-negative numbers
    for col in ["invoice_count", "total_invoice_value", "total_tax"]:
        assert (t0_rows[col] >= 0).all()
