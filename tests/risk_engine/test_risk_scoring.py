"""
Unit tests for ML Risk Indicator Score and presentation risk bands.
Verifies exact deterministic scoring formula and model_class vs risk_band separation.
"""

import pytest
from backend.ml.risk_engine import ITCRiskEngine


def test_exact_risk_score_formula_cases():
    """Verifies mandatory Section 23 scoring cases."""
    engine = ITCRiskEngine()

    # Case 1: P(Medium)=0, P(High)=0 -> score=0
    assert engine.calculate_risk_score({"LOW": 1.0, "MEDIUM": 0.0, "HIGH": 0.0}) == 0.0

    # Case 2: P(Medium)=1, P(High)=0 -> score=50
    assert engine.calculate_risk_score({"LOW": 0.0, "MEDIUM": 1.0, "HIGH": 0.0}) == 50.0

    # Case 3: P(Medium)=0, P(High)=1 -> score=100
    assert engine.calculate_risk_score({"LOW": 0.0, "MEDIUM": 0.0, "HIGH": 1.0}) == 100.0

    # Case 4: P(Low)=0.2, P(Medium)=0.3, P(High)=0.5 -> score=65 (100 * (0.3*0.5 + 0.5*1.0) = 65)
    assert engine.calculate_risk_score({"LOW": 0.2, "MEDIUM": 0.3, "HIGH": 0.5}) == 65.0


def test_risk_score_range_and_clipping():
    """Verifies risk score is strictly bounded between 0.0 and 100.0."""
    engine = ITCRiskEngine()
    assert 0.0 <= engine.calculate_risk_score({"LOW": 0.5, "MEDIUM": 0.25, "HIGH": 0.25}) <= 100.0
    assert engine.calculate_risk_score({"LOW": -0.5, "MEDIUM": 0.0, "HIGH": 1.5}) == 100.0


def test_presentation_risk_band_mapping():
    """Verifies application presentation thresholds: 0-33 LOW, >33-66 MEDIUM, >66-100 HIGH."""
    engine = ITCRiskEngine()
    assert engine.get_risk_band(0.0) == "LOW"
    assert engine.get_risk_band(33.0) == "LOW"
    assert engine.get_risk_band(33.1) == "MEDIUM"
    assert engine.get_risk_band(50.0) == "MEDIUM"
    assert engine.get_risk_band(66.0) == "MEDIUM"
    assert engine.get_risk_band(66.1) == "HIGH"
    assert engine.get_risk_band(100.0) == "HIGH"


def test_model_class_and_risk_band_separation():
    """
    Section 24: Verifies model_class and risk_band are separately represented and not conflated.
    Example: A model predicting MEDIUM with probabilities yielding score 67.2 has model_class=MEDIUM, risk_band=HIGH.
    """
    engine = ITCRiskEngine()
    # P(Medium)=0.35, P(High)=0.50 -> Score: 100 * (0.175 + 0.50) = 67.5 -> band: HIGH, but argmax is HIGH
    # To get model_class=MEDIUM and risk_band=HIGH:
    # Say probabilities: LOW=0.05, MEDIUM=0.48, HIGH=0.47 -> argmax is MEDIUM.
    # Score = 100 * (0.48 * 0.5 + 0.47 * 1.0) = 100 * (0.24 + 0.47) = 71.0 -> band: HIGH.
    probs = {"LOW": 0.05, "MEDIUM": 0.48, "HIGH": 0.47}
    score = engine.calculate_risk_score(probs)
    band = engine.get_risk_band(score)

    assert score == 71.0
    assert band == "HIGH"
    # Argmax is MEDIUM
    model_class = max(probs, key=probs.get)
    assert model_class == "MEDIUM"
    # Proves model_class != band in boundary transitions without conflation
    assert model_class != band
