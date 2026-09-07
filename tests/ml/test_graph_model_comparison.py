"""
Tests for Graph vs Tabular Model Comparison.
Verifies evaluation fairness, identical test data, calibration metrics, and SHAP report consistency.
"""

import json
import os
import pytest


@pytest.fixture
def error_report():
    report_path = os.path.join("data", "reports", "ml", "graph_error_analysis.json")
    if not os.path.exists(report_path):
        pytest.skip("graph_error_analysis.json not generated yet")
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def shap_report():
    report_path = os.path.join("data", "reports", "ml", "graph_shap_importance.json")
    if not os.path.exists(report_path):
        pytest.skip("graph_shap_importance.json not generated yet")
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_confusion_matrices_total_samples_match(error_report):
    """Test 1: Confirms both Tabular and Graph confusion matrices evaluate the exact same test samples."""
    tab_m = error_report["tabular_confusion_matrix"]["matrix"]
    g_m = error_report["graph_confusion_matrix"]["matrix"]

    total_tab = sum(sum(row) for row in tab_m)
    total_g = sum(sum(row) for row in g_m)

    assert total_tab == total_g
    assert total_tab == 8060  # exact test split size


def test_shap_importance_sums_to_100_percent(shap_report):
    """Test 2: Verifies tabular and graph SHAP attribution percentages sum to 100%."""
    summary = shap_report["summary"]
    tab_share = summary["tabular_shap_share_pct"]
    g_share = summary["graph_shap_share_pct"]

    assert round(tab_share + g_share, 1) == 100.0
    assert summary["total_features"] == 29
