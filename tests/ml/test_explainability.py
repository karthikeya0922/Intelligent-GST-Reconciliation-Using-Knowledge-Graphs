"""
Unit tests for multiclass Tree SHAP and class-specific model explainability.
"""
import pytest
import numpy as np
import xgboost as xgb
from backend.ml.explain import ModelExplainer

def test_class_specific_tree_shap():
    """Verify ModelExplainer provides per-class Tree SHAP attributions."""
    X = np.array([
        [1.0, 0.05, 100.0],
        [5.0, 0.50, 500.0],
        [10.0, 0.90, 1000.0]
    ])
    y = np.array([0, 1, 2])
    feature_names = ["inv_count", "mismatch_rate", "tax"]
    
    clf = xgb.XGBClassifier(n_estimators=5, max_depth=2, random_state=42)
    clf.fit(X, y)
    
    explainer = ModelExplainer(clf, feature_names)
    
    # 1. Test global importance
    global_imp = explainer.compute_global_feature_importance(X)
    assert "overall_importance" in global_imp
    assert "per_class_importance" in global_imp
    assert "Low" in global_imp["per_class_importance"]
    assert "Medium" in global_imp["per_class_importance"]
    assert "High" in global_imp["per_class_importance"]
    
    # 2. Test local instance explanation
    local_exp = explainer.explain_vendor_instance(X[0], top_k=2)
    assert "predicted_class" in local_exp
    assert "predicted_probabilities" in local_exp
    assert "target_class_explanation" in local_exp
    assert len(local_exp["target_class_explanation"]) <= 2
    for factor in local_exp["target_class_explanation"]:
        assert "feature" in factor
        assert "shap_value" in factor
        assert "effect" in factor
