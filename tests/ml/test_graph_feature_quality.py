"""
Tests for Graph Feature Quality Audit.
Verifies data quality statistics, zero-inflation, variance, and collinearity identification.
"""

import json
import os
import pytest
from backend.ml.graph_features import GRAPH_FEATURE_NAMES


@pytest.fixture
def quality_report():
    report_path = os.path.join("data", "reports", "ml", "graph_feature_quality.json")
    if not os.path.exists(report_path):
        pytest.skip("graph_feature_quality.json not generated yet")
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_all_graph_features_audited(quality_report):
    """Test 1: Confirms all 10 graph features have complete quality audit entries."""
    metrics = quality_report["feature_metrics"]
    assert len(metrics) == len(GRAPH_FEATURE_NAMES)
    for feat in GRAPH_FEATURE_NAMES:
        assert feat in metrics
        assert "zero_percentage" in metrics[feat]
        assert "missing_percentage" in metrics[feat]
        assert "unique_values_count" in metrics[feat]


def test_redundant_and_constant_flags_consistency(quality_report):
    """Test 2: Verifies summary flags match individual feature metric evaluations."""
    metrics = quality_report["feature_metrics"]
    summary = quality_report["summary"]

    for feat, m in metrics.items():
        if m["is_constant"]:
            assert feat in summary["constant_features"]
        if m["is_redundant"]:
            assert feat in summary["redundant_features"]
            assert len(m["redundant_with"]) > 0
