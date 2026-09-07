"""
Unit tests for model artifact serialization and reloading.
"""
import pytest
import os
import json
import joblib
from sklearn.ensemble import RandomForestClassifier
from backend.ml.preprocessing import build_preprocessor

def test_model_persistence_and_reloading(tmp_path):
    """Verify models and metadata can be cleanly persisted and reloaded without loss."""
    meta_path = os.path.join(tmp_path, "model_metadata.json")
    model_path = os.path.join(tmp_path, "best_tabular_model.pkl")
    
    metadata = {
        "model_version": "2.0.0",
        "dataset_version": "1.5.0",
        "feature_names": ["invoice_count", "mismatch_rate"],
        "class_names": ["Low", "Medium", "High"]
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f)
        
    clf = RandomForestClassifier(n_estimators=5, random_state=42)
    clf.fit([[1, 0.1], [2, 0.5], [3, 0.9]], [0, 1, 2])
    joblib.dump(clf, model_path)
    
    # Reload
    reloaded_clf = joblib.load(model_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        reloaded_meta = json.load(f)
        
    assert reloaded_meta["model_version"] == "2.0.0"
    preds_orig = clf.predict([[1, 0.1]])
    preds_reloaded = reloaded_clf.predict([[1, 0.1]])
    assert preds_orig[0] == preds_reloaded[0]
