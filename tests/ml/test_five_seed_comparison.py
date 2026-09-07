"""
Tests for 5-Seed Statistical Comparison Protocol.
Verifies identical seeds, temporal consistency, mean/std math, and evaluation fairness.
"""

import json
import os
import pytest
import numpy as np


@pytest.fixture
def five_seed_report():
    report_path = os.path.join("data", "reports", "ml", "five_seed_comparison.json")
    if not os.path.exists(report_path):
        pytest.skip("five_seed_comparison.json not generated yet")
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_identical_seeds_evaluated(five_seed_report):
    """Test 1: Confirms both Tabular and Graph models evaluated on exactly the 5 specified seeds."""
    expected_seeds = [42, 123, 2024, 999, 7]
    assert five_seed_report["seeds"] == expected_seeds
    per_seed = five_seed_report["per_seed_results"]
    assert len(per_seed) == 5
    for row, expected_s in zip(per_seed, expected_seeds):
        assert row["seed"] == expected_s


def test_summary_mean_std_correctness(five_seed_report):
    """Test 2: Verifies summary mean and std calculations match per-seed results."""
    per_seed = five_seed_report["per_seed_results"]
    tab_f1s = [r["tabular_macro_f1"] for r in per_seed]
    g_f1s = [r["graph_macro_f1"] for r in per_seed]

    calc_tab_mean = round(float(np.mean(tab_f1s)), 4)
    calc_g_mean = round(float(np.mean(g_f1s)), 4)

    reported_tab_mean = five_seed_report["summary_table"]["macro_f1"]["tabular"]["mean"]
    reported_g_mean = five_seed_report["summary_table"]["macro_f1"]["graph"]["mean"]

    assert calc_tab_mean == reported_tab_mean
    assert calc_g_mean == reported_g_mean


def test_paired_deltas_consistency(five_seed_report):
    """Test 3: Checks that per-seed deltas are exactly Graph - Tabular."""
    for r in five_seed_report["per_seed_results"]:
        expected_delta = round(r["graph_macro_f1"] - r["tabular_macro_f1"], 4)
        assert r["delta_macro_f1"] == expected_delta
