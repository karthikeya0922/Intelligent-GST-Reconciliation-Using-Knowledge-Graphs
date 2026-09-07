"""
Production Prediction & Inference Service for GST Risk Models.

Loads persisted preprocessing and model artifacts, evaluates single or batch
vendor observations, and provides structured prediction outputs with top
risk factors.
"""

from typing import List, Dict, Any, Optional
import os
import json
import joblib
import numpy as np
import pandas as pd

from backend.ml.explain import ModelExplainer
from backend.ml.features import engineer_derived_features


DEFAULT_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models")


class GSTVendorRiskPredictor:
    """Production predictor serving model predictions and local factor attributions."""

    def __init__(self, models_dir: str = DEFAULT_MODELS_DIR):
        self.models_dir = models_dir
        self.model = None
        self.preprocessor = None
        self.metadata = None
        self.feature_names = []
        self._load_artifacts()

    def _load_artifacts(self):
        """Loads serialized model, preprocessor, and metadata from models_dir."""
        meta_path = os.path.join(self.models_dir, "model_metadata.json")
        prep_path = os.path.join(self.models_dir, "preprocessing.pkl")
        
        # Prefer graph-enhanced model if available, otherwise tabular
        graph_model_path = os.path.join(self.models_dir, "best_graph_enhanced_model.pkl")
        tabular_model_path = os.path.join(self.models_dir, "best_tabular_model.pkl")

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
                self.feature_names = self.metadata.get("feature_names", [])

        if os.path.exists(prep_path):
            self.preprocessor = joblib.load(prep_path)

        if os.path.exists(graph_model_path):
            self.model = joblib.load(graph_model_path)
        elif os.path.exists(tabular_model_path):
            self.model = joblib.load(tabular_model_path)

    def predict(
        self,
        vendor_id: str,
        period: str,
        record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predicts next-period risk class, probabilities, and top risk factors for a vendor.
        """
        if self.model is None or not self.feature_names:
            # Graceful rule fallback if model is not yet trained/loaded
            return self._heuristic_fallback(vendor_id, period, record)

        # Convert record to 1-row DataFrame
        df = pd.DataFrame([record])
        df = engineer_derived_features(df)

        # Ensure all required features are present
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0.0

        X = df[self.feature_names]
        if self.preprocessor is not None:
            try:
                X_trans = self.preprocessor.transform(X)
            except Exception:
                X_trans = X.to_numpy()
        else:
            X_trans = X.to_numpy()

        probs = self.model.predict_proba(X_trans)[0]
        # Normalize probabilities to sum exactly to 1.0
        probs = np.maximum(probs, 0.0)
        prob_sum = probs.sum()
        if prob_sum > 0:
            probs = probs / prob_sum
        else:
            probs = np.array([0.70, 0.20, 0.10])

        class_idx = int(np.argmax(probs))
        class_names = ["LOW", "MEDIUM", "HIGH"]
        predicted_class = class_names[class_idx]

        # Extract top contributing factors via ModelExplainer
        explainer = ModelExplainer(self.model, self.feature_names)
        explanation = explainer.explain_vendor_instance(X_trans, top_k=3)
        target_factors = explanation.get("target_class_explanation", [])

        top_factors = []
        for factor in target_factors:
            val = abs(factor.get("shap_value", 0.0))
            impact = "high" if val > 0.15 else ("medium" if val > 0.05 else "low")
            top_factors.append({
                "feature": factor.get("feature", "unknown"),
                "impact": impact
            })

        return {
            "vendor_id": vendor_id,
            "period": period,
            "risk_class": predicted_class,
            "risk_probability": {
                "LOW": round(float(probs[0]), 4),
                "MEDIUM": round(float(probs[1]), 4),
                "HIGH": round(float(probs[2]), 4)
            },
            "top_factors": top_factors
        }

    def _heuristic_fallback(self, vendor_id: str, period: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback prediction when trained model weights are uninitialized."""
        mismatch_rate = float(record.get("mismatch_rate", 0.0))
        delay = float(record.get("average_filing_delay", 0.0))
        
        if mismatch_rate > 0.40 or delay > 10:
            r_class = "HIGH"
            p = {"LOW": 0.08, "MEDIUM": 0.12, "HIGH": 0.80}
            factors = [{"feature": "mismatch_rate", "impact": "high"}]
        elif mismatch_rate > 0.15 or delay > 3:
            r_class = "MEDIUM"
            p = {"LOW": 0.20, "MEDIUM": 0.65, "HIGH": 0.15}
            factors = [{"feature": "average_filing_delay", "impact": "medium"}]
        else:
            r_class = "LOW"
            p = {"LOW": 0.85, "MEDIUM": 0.10, "HIGH": 0.05}
            factors = [{"feature": "invoice_count", "impact": "low"}]

        return {
            "vendor_id": vendor_id,
            "period": period,
            "risk_class": r_class,
            "risk_probability": p,
            "top_factors": factors
        }


# Singleton instance
_predictor = None

def get_predictor(models_dir: str = DEFAULT_MODELS_DIR) -> GSTVendorRiskPredictor:
    global _predictor
    if _predictor is None:
        _predictor = GSTVendorRiskPredictor(models_dir=models_dir)
    return _predictor
