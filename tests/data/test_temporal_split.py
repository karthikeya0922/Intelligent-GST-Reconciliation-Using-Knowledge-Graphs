"""
Tests for temporal dataset splitting and partition validation.
"""
import pytest
from backend.data.synthetic.generator import SyntheticGSTGenerator
from backend.data.features.aggregator import VendorPeriodFeatureAggregator, split_temporal_dataset, validate_split_balance

def test_temporal_dataset_partition():
    """Verify temporal splitting into train, validation, and test sets."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=30, months_count=14)
    
    aggregator = VendorPeriodFeatureAggregator()
    df = aggregator.build_feature_matrix(
        dataset["vendors"],
        dataset["invoices"],
        dataset["reconciliations"],
        dataset["filings"],
        dataset["tax_periods"]
    )
    
    tax_periods = dataset["tax_periods"]
    splits = aggregator.split_temporal_dataset(df, tax_periods)
    
    train_df = splits["train"]
    val_df = splits["validation"]
    test_df = splits["test"]
    
    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0
    assert len(train_df) + len(val_df) + len(test_df) == len(df)
    
    # Verify strict temporal ordering
    train_periods = set(train_df["prediction_period"])
    val_periods = set(val_df["prediction_period"])
    test_periods = set(test_df["prediction_period"])
    
    assert max(train_periods) < min(val_periods)
    assert max(val_periods) < min(test_periods)

def test_temporal_boundary_fields():
    """Verify that feature rows contain explicit temporal boundary fields."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=20, months_count=6)
    
    aggregator = VendorPeriodFeatureAggregator()
    df = aggregator.build_feature_matrix(
        dataset["vendors"],
        dataset["invoices"],
        dataset["reconciliations"],
        dataset["filings"],
        dataset["tax_periods"]
    )
    
    expected_cols = ["prediction_period", "feature_period_start", "feature_period_end", "target_period"]
    for col in expected_cols:
        assert col in df.columns, f"Missing temporal boundary column: {col}"
    
    # Check that for any row, feature_period_start <= feature_period_end == prediction_period < target_period
    for _, row in df.iterrows():
        assert row["feature_period_start"] <= row["feature_period_end"]
        assert row["feature_period_end"] == row["prediction_period"]
        assert row["prediction_period"] < row["target_period"]

def test_validate_split_balance():
    """Verify validate_split_balance checks representation across all splits."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=40, months_count=12)
    
    aggregator = VendorPeriodFeatureAggregator()
    df = aggregator.build_feature_matrix(
        dataset["vendors"],
        dataset["invoices"],
        dataset["reconciliations"],
        dataset["filings"],
        dataset["tax_periods"]
    )
    
    splits = aggregator.split_temporal_dataset(df, dataset["tax_periods"])
    balance_report = validate_split_balance(splits)
    
    assert balance_report["valid"] is True
    assert "train" in balance_report["splits"]
    assert "validation" in balance_report["splits"]
    assert "test" in balance_report["splits"]
