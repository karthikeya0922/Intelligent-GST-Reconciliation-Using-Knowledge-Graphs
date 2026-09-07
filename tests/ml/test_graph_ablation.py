"""
Tests for Graph Feature Ablation.
Verifies deterministic group definitions, structure, and validation-based evaluation protocol.
"""

import json
import os
import pytest
from backend.ml.phase2_1_validator import GRAPH_FEATURE_GROUPS
from backend.ml.graph_features import GRAPH_FEATURE_NAMES


@pytest.fixture
def ablation_report():
    report_path = os.path.join("data", "reports", "ml", "graph_feature_ablation.json")
    if not os.path.exists(report_path):
        pytest.skip("graph_feature_ablation.json not generated yet")
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_graph_groups_deterministic_and_complete():
    """Test 1: Confirms all 10 graph features belong to exactly one defined group."""
    all_grouped_features = []
    for grp_name, feat_list in GRAPH_FEATURE_GROUPS.items():
        assert len(feat_list) > 0
        all_grouped_features.extend(feat_list)

    assert sorted(all_grouped_features) == sorted(GRAPH_FEATURE_NAMES)
    assert len(all_grouped_features) == len(set(all_grouped_features))


def test_ablation_report_structure(ablation_report):
    """Test 2: Confirms forward addition and leave-one-out stages are recorded with validation & test metrics."""
    fwd = ablation_report["forward_addition"]
    loo = ablation_report["leave_one_group_out"]

    assert len(fwd) == 6
    assert len(loo) == 5

    for stage_name, metrics in fwd.items():
        assert "validation_macro_f1" in metrics
        assert "test_macro_f1" in metrics
        assert metrics["num_features"] >= 19

    for stage_name, metrics in loo.items():
        assert "validation_macro_f1" in metrics
        assert "test_macro_f1" in metrics
        assert metrics["num_features"] < 29
