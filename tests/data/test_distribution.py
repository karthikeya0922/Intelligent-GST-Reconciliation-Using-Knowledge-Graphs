"""
Tests for statistical distribution analysis and reporting.
"""
import pytest
import os
import pandas as pd
from backend.data.distribution_analyzer import DistributionAnalyzer
from backend.data.synthetic.generator import SyntheticGSTGenerator
from backend.data.features.aggregator import VendorPeriodFeatureAggregator

def test_distribution_analyzer_statistics():
    """Verify DistributionAnalyzer computes full descriptive statistics for numerical features."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=25, months_count=6)
    
    aggregator = VendorPeriodFeatureAggregator()
    df = aggregator.build_feature_matrix(
        dataset["vendors"],
        dataset["invoices"],
        dataset["reconciliations"],
        dataset["filings"],
        dataset["tax_periods"]
    )
    
    analyzer = DistributionAnalyzer()
    stats = analyzer.compute_feature_statistics(df)
    
    assert len(stats) > 0
    # Check that standard features exist
    assert "invoice_count" in stats
    inv_stat = stats["invoice_count"]
    assert "mean" in inv_stat
    assert "std" in inv_stat
    assert "min" in inv_stat
    assert "p50" in inv_stat
    assert "max" in inv_stat
    assert "skewness" in inv_stat
    assert inv_stat["min"] >= 0

def test_distribution_anomaly_detection():
    """Verify DistributionAnalyzer detects potential data issues or passes valid clean data."""
    analyzer = DistributionAnalyzer()
    # Create synthetic dataframe with a high correlation and negative amount to test warning detection
    df = pd.DataFrame({
        "feature_a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "feature_b": [2.0, 4.0, 6.0, 8.0, 10.0],  # Correlation = 1.0 with feature_a
        "feature_neg": [-10.0, 0.0, 10.0, 20.0, 30.0],  # Negative value
        "feature_zero_var": [5.0, 5.0, 5.0, 5.0, 5.0]  # Variance = 0
    })
    
    anomalies = analyzer.detect_distribution_anomalies(df)
    assert len(anomalies) >= 2
    # Verify extreme correlation was flagged
    corr_flags = [a for a in anomalies if a["type"] == "EXTREME_CORRELATION"]
    assert len(corr_flags) > 0
    # Verify zero variance was flagged
    var_flags = [a for a in anomalies if a["type"] == "NEAR_ZERO_VARIANCE"]
    assert len(var_flags) > 0

def test_report_generation(tmp_path):
    """Verify full report generation produces valid JSON and Markdown files."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=20, months_count=4)
    
    aggregator = VendorPeriodFeatureAggregator()
    df = aggregator.build_feature_matrix(
        dataset["vendors"],
        dataset["invoices"],
        dataset["reconciliations"],
        dataset["filings"],
        dataset["tax_periods"]
    )
    
    analyzer = DistributionAnalyzer()
    report = analyzer.generate_report(df, dataset["invoices"], output_dir=str(tmp_path))
    
    assert "feature_statistics" in report
    assert "distribution_anomalies" in report
    assert os.path.exists(os.path.join(str(tmp_path), "feature_distribution_report.json"))
    assert os.path.exists(os.path.join(str(tmp_path), "feature_distribution_report.md"))
