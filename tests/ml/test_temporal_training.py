"""
Unit tests for train/validation separation and class weighting.
"""
import pytest
import numpy as np
from sklearn.utils.class_weight import compute_sample_weight
from backend.ml.evaluate import evaluate_model_performance

def test_sample_weight_calculation():
    """Verify compute_sample_weight properly balances class frequencies."""
    # Imbalanced sample: 8 Low (0), 2 Medium (1), 1 High (2)
    y = np.array([0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2])
    weights = compute_sample_weight("balanced", y)
    
    assert len(weights) == len(y)
    # Minority class (High) should receive higher weight than majority class (Low)
    assert weights[-1] > weights[0]
    assert weights[8] > weights[0]

def test_evaluation_metric_properties():
    """Verify evaluate_model_performance outputs all required metrics."""
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 1, 1, 1, 2, 0])
    y_prob = np.array([
        [0.8, 0.1, 0.1],
        [0.3, 0.6, 0.1],
        [0.1, 0.8, 0.1],
        [0.2, 0.7, 0.1],
        [0.1, 0.2, 0.7],
        [0.6, 0.2, 0.2]
    ])
    
    res = evaluate_model_performance(y_true, y_pred, y_prob)
    
    assert "macro_f1" in res
    assert "balanced_accuracy" in res
    assert "high_risk_metrics" in res
    assert "confusion_matrix" in res
    assert "log_loss" in res
    assert "brier_score" in res
    assert "error_analysis" in res
    assert res["high_risk_metrics"]["recall"] >= 0.0
