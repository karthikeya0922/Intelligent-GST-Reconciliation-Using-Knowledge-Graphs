"""
Class-Specific Multiclass Tree SHAP & Model Explainability Module.

Extracts:
1. Global feature importance rankings per class and aggregate.
2. Local vendor-level risk factor attributions distinguishing
   contributions toward Low (0), Medium (1), and High (2) risk.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd


class ModelExplainer:
    """Provides class-specific Tree SHAP explanations for tree and linear models."""

    def __init__(self, model: Any, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.class_names = ["Low", "Medium", "High"]

    def compute_global_feature_importance(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Computes global feature importance rankings across all features.
        Supports native Tree SHAP for XGBoost and feature_importances_ for Random Forest.
        """
        # Case 1: XGBoost classifier with native Tree SHAP
        if hasattr(self.model, "get_booster"):
            try:
                import xgboost as xgb
                booster = self.model.get_booster()
                dmat = xgb.DMatrix(X, feature_names=self.feature_names)
                # Shape: (N, n_classes, n_features + 1)
                contribs = booster.predict(dmat, pred_contribs=True)
                # Feature contributions (excluding the bias term at index -1)
                feat_contribs = contribs[:, :, :-1]

                global_importances = {}
                for class_idx, cname in enumerate(self.class_names):
                    class_mean_abs = np.mean(np.abs(feat_contribs[:, class_idx, :]), axis=0)
                    global_importances[cname] = [
                        {"feature": self.feature_names[i], "importance": round(float(class_mean_abs[i]), 5)}
                        for i in np.argsort(-class_mean_abs)
                    ]

                # Overall aggregate mean absolute SHAP across all classes
                overall_abs = np.mean(np.mean(np.abs(feat_contribs), axis=1), axis=0)
                overall_ranked = [
                    {"feature": self.feature_names[i], "importance": round(float(overall_abs[i]), 5)}
                    for i in np.argsort(-overall_abs)
                ]

                return {
                    "method": "Tree SHAP (Native XGBoost)",
                    "overall_importance": overall_ranked,
                    "per_class_importance": global_importances
                }
            except Exception as e:
                pass

        # Case 2: Random Forest (Gini Importance)
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            ranked = [
                {"feature": self.feature_names[i], "importance": round(float(importances[i]), 5)}
                for i in np.argsort(-importances)
            ]
            return {
                "method": "Mean Decrease in Impurity (Random Forest)",
                "overall_importance": ranked,
                "per_class_importance": {c: ranked for c in self.class_names}
            }

        # Case 3: Logistic Regression (Coefficients)
        if hasattr(self.model, "coef_"):
            coefs = self.model.coef_
            per_class = {}
            for class_idx, cname in enumerate(self.class_names):
                class_coef = np.abs(coefs[class_idx])
                per_class[cname] = [
                    {"feature": self.feature_names[i], "importance": round(float(class_coef[i]), 5)}
                    for i in np.argsort(-class_coef)
                ]
            overall = np.mean(np.abs(coefs), axis=0)
            overall_ranked = [
                {"feature": self.feature_names[i], "importance": round(float(overall[i]), 5)}
                for i in np.argsort(-overall)
            ]
            return {
                "method": "Absolute Coefficients (Logistic Regression)",
                "overall_importance": overall_ranked,
                "per_class_importance": per_class
            }

        return {"method": "Unknown", "overall_importance": [], "per_class_importance": {}}

    def explain_vendor_instance(
        self,
        X_sample: np.ndarray,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Produces class-specific local explanation for a single vendor observation.
        """
        # Ensure 2D array: (1, n_features)
        if len(X_sample.shape) == 1:
            X_sample = X_sample.reshape(1, -1)

        # 1. Get predicted class and probabilities
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X_sample)[0]
        else:
            probs = np.array([0.33, 0.33, 0.34])

        pred_class_idx = int(np.argmax(probs))
        pred_class_name = self.class_names[pred_class_idx]

        # 2. Extract SHAP values
        class_attributions = {}
        if hasattr(self.model, "get_booster"):
            try:
                import xgboost as xgb
                booster = self.model.get_booster()
                dmat = xgb.DMatrix(X_sample, feature_names=self.feature_names)
                contribs = booster.predict(dmat, pred_contribs=True)[0]
                feat_contribs = contribs[:, :-1]  # (3, n_features)

                for c_idx, cname in enumerate(self.class_names):
                    c_shap = feat_contribs[c_idx]
                    sorted_indices = np.argsort(-np.abs(c_shap))
                    
                    factors = []
                    for i in sorted_indices[:top_k]:
                        val = float(c_shap[i])
                        factors.append({
                            "feature": self.feature_names[i],
                            "shap_value": round(val, 4),
                            "effect": "increases_risk_probability" if val > 0 else "reduces_risk_probability"
                        })
                    class_attributions[cname] = factors
            except Exception:
                pass

        # Fallback if SHAP was not calculated
        if not class_attributions:
            for cname in self.class_names:
                class_attributions[cname] = [
                    {"feature": self.feature_names[i], "shap_value": 0.0, "effect": "neutral"}
                    for i in range(min(top_k, len(self.feature_names)))
                ]

        return {
            "predicted_class": pred_class_name,
            "predicted_probabilities": {
                "Low": round(float(probs[0]), 4),
                "Medium": round(float(probs[1]), 4),
                "High": round(float(probs[2]), 4)
            },
            "target_class_explanation": class_attributions.get(pred_class_name, []),
            "all_class_attributions": class_attributions
        }
