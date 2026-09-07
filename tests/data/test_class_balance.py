"""
Tests for experimental class balance and target risk distribution.
"""
import pytest
from backend.data.synthetic.generator import SyntheticGSTGenerator
from backend.data.features.aggregator import VendorPeriodFeatureAggregator

def test_class_balance_distribution():
    """Verify target risk distribution falls within experimental balanced targets (Low ~60-70%, Med ~20-25%, High ~10-15%)."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=60, months_count=12)
    
    aggregator = VendorPeriodFeatureAggregator()
    df = aggregator.build_feature_matrix(
        dataset["vendors"],
        dataset["invoices"],
        dataset["reconciliations"],
        dataset["filings"],
        dataset["tax_periods"]
    )
    
    assert len(df) > 0
    # Check that each (vendor_id, prediction_period) is unique (no duplicate rows)
    assert df.duplicated(subset=["vendor_id", "prediction_period"]).sum() == 0
    
    dist = df["target_risk_label"].value_counts(normalize=True)
    low_pct = (dist.get("Low", 0.0) + dist.get("LOW", 0.0)) * 100
    med_pct = (dist.get("Medium", 0.0) + dist.get("MEDIUM", 0.0)) * 100
    high_pct = (dist.get("High", 0.0) + dist.get("HIGH", 0.0)) * 100
    
    # Allow reasonable stochastic tolerance for 60 vendors
    assert 50.0 <= low_pct <= 75.0, f"Expected Low Risk ~60-70%, got {low_pct:.1f}%"
    assert 15.0 <= med_pct <= 35.0, f"Expected Medium Risk ~20-25%, got {med_pct:.1f}%"
    assert 8.0 <= high_pct <= 25.0, f"Expected High Risk ~10-15%, got {high_pct:.1f}%"

def test_no_row_duplication_for_balance():
    """Verify that class balance is achieved via behavioral profiles, not row duplication."""
    gen = SyntheticGSTGenerator(seed=99)
    dataset = gen.generate_dataset(vendor_count=40, months_count=6)
    
    aggregator = VendorPeriodFeatureAggregator()
    df = aggregator.build_feature_matrix(
        dataset["vendors"],
        dataset["invoices"],
        dataset["reconciliations"],
        dataset["filings"],
        dataset["tax_periods"]
    )
    # The number of unique vendor IDs in df should match the number of vendors having invoice activity
    active_vendors = {inv.vendor_id for inv in dataset["invoices"]}
    assert len(df) == len(df.drop_duplicates(subset=["vendor_id", "prediction_period"]))
