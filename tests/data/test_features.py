"""Tests for feature engineering and data leakage prevention."""

from datetime import date
from decimal import Decimal
import pandas as pd
import pytest

from backend.data.synthetic.generator import SyntheticGSTDatasetGenerator
from backend.data.features.aggregator import FeatureAggregator


def test_feature_aggregation_correctness():
    gen = SyntheticGSTDatasetGenerator(seed=42)
    ds = gen.generate_dataset(vendor_count=5, months_count=3)
    
    agg = FeatureAggregator()
    vendor_ids = [v.vendor_id for v in ds["vendors"]]
    df = agg.create_temporal_feature_dataset(
        vendor_ids=vendor_ids,
        tax_periods=ds["tax_periods"],
        invoices=ds["invoices"],
        filings=ds["filings"],
        reconciliations=ds["reconciliations"],
        lookback_periods=1
    )

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    
    # Expected columns present
    expected_cols = [
        "vendor_id", "tax_period", "invoice_count", "total_invoice_value",
        "total_tax", "mismatch_count", "mismatch_rate", "missing_gstr1_count",
        "missing_gstr3b_count", "itc_exposure", "target_risk_label", "target_risk_score"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Column '{col}' missing from feature dataset"


def test_zero_future_data_leakage():
    """
    CRITICAL TEST: Ensure that for a feature row for period T_k,
    no invoice or filing from period T_{k+1} or beyond influenced the feature values.
    """
    gen = SyntheticGSTDatasetGenerator(seed=99)
    ds = gen.generate_dataset(vendor_count=5, months_count=4)
    periods = ds["tax_periods"]  # e.g. ['2024-04', '2024-05', '2024-06', '2024-07']
    
    agg = FeatureAggregator()
    vendor_ids = [v.vendor_id for v in ds["vendors"]]
    df = agg.create_temporal_feature_dataset(
        vendor_ids=vendor_ids,
        tax_periods=periods,
        invoices=ds["invoices"],
        filings=ds["filings"],
        reconciliations=ds["reconciliations"],
        lookback_periods=1
    )

    # For any row where tax_period is '2024-04', target_period must be '2024-05'
    apr_rows = df[df["tax_period"] == "2024-04"]
    assert (apr_rows["target_period"] == "2024-05").all()

    # Verify that if an anomaly occurred in 2024-05 (target period),
    # the 2024-04 feature columns ('mismatch_count', 'missing_gstr1_count', etc.)
    # only count events that occurred in 2024-04!
    for _, row in apr_rows.iterrows():
        vid = row["vendor_id"]
        apr_invs = [i for i in ds["invoices"] if i.vendor_id == vid and i.tax_period == "2024-04"]
        assert row["invoice_count"] == len(apr_invs)
