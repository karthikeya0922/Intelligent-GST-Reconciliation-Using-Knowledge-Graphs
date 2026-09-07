"""
Unit tests for vendor risk history and trend analysis.
Verifies temporal causality, transition logging, and trend detection.
"""

import pytest
from backend.ml.risk_engine import ITCRiskEngine


def test_vendor_risk_history_chronology():
    """Verifies history entries are strictly sorted chronologically by tax period."""
    engine = ITCRiskEngine()
    history = engine.get_vendor_history("V0001")

    if len(history) > 1:
        periods = [h["period"] for h in history]
        assert periods == sorted(periods)
        for entry in history:
            assert "period" in entry
            assert "risk_class" in entry
            assert "risk_score" in entry
            assert 0.0 <= entry["risk_score"] <= 100.0


def test_vendor_risk_trend_and_transitions():
    """Verifies transitions and trend evaluation logic."""
    engine = ITCRiskEngine()
    trend_data = engine.get_risk_trend("V0001")

    assert "trend" in trend_data
    assert trend_data["trend"] in ["stable", "improving", "deteriorating", "volatile", "unknown"]
    assert "transitions" in trend_data
    assert "history_length" in trend_data

    if trend_data["transitions"]:
        sample_trans = trend_data["transitions"][0]
        assert "period_transition" in sample_trans
        assert "class_transition" in sample_trans
        assert "score_delta" in sample_trans
