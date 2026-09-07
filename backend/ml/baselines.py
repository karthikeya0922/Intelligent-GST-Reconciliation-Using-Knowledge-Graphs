"""
Non-Machine Learning Baseline Models.

1. MajorityBaseline:
   Always predicts the majority class ("Low" / 0).

2. RuleBasedBaseline:
   Calculates the Phase 1.5 experimental composite risk penalty score from
   available features at T_k and applies experimental decision thresholds:
       < 0.20  -> Low (0)
       0.20-0.50 -> Medium (1)
       >= 0.50 -> High (2)
   NOTE: These thresholds are experimental research rules, NOT statutory government
   classifications.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd


class MajorityBaseline:
    """Predicts majority class (0 / Low) unconditionally."""

    def __init__(self, majority_class: int = 0):
        self.majority_class = majority_class

    def fit(self, X: Any, y: Any = None):
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        n_samples = len(X)
        return np.full(n_samples, self.majority_class, dtype=int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        n_samples = len(X)
        proba = np.zeros((n_samples, 3), dtype=float)
        proba[:, self.majority_class] = 1.0
        return proba


class RuleBasedBaseline:
    """
    Experimental rule-based heuristic baseline.
    Uses Phase 1.5 composite penalty weights applied strictly to features at T_k.
    """

    def __init__(self):
        # Phase 1.5 experimental weights
        self.weights = {
            "missing_gstr3b_penalty": 0.35,
            "missing_gstr1_penalty": 0.25,
            "mismatch_rate_penalty": 0.25,
            "filing_delay_penalty": 0.10,
            "duplicate_penalty": 0.05
        }

    def fit(self, X: Any, y: Any = None):
        return self

    def _compute_score(self, row: pd.Series) -> float:
        missing_3b = 1.0 if row.get("missing_gstr3b_count", 0) > 0 else 0.0
        missing_1 = 1.0 if row.get("missing_gstr1_count", 0) > 0 else 0.0
        mismatch_r = float(min(row.get("mismatch_rate", 0.0), 1.0))
        delay = float(row.get("average_filing_delay", 0.0))
        norm_delay = min(delay / 30.0, 1.0)
        dup = 1.0 if row.get("duplicate_invoice_count", 0) > 0 else 0.0

        score = (
            missing_3b * self.weights["missing_gstr3b_penalty"]
            + missing_1 * self.weights["missing_gstr1_penalty"]
            + mismatch_r * self.weights["mismatch_rate_penalty"]
            + norm_delay * self.weights["filing_delay_penalty"]
            + dup * self.weights["duplicate_penalty"]
        )
        return min(max(score, 0.0), 1.0)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        preds = []
        for _, row in X.iterrows():
            score = self._compute_score(row)
            if score < 0.20:
                preds.append(0)  # Low
            elif score < 0.50:
                preds.append(1)  # Medium
            else:
                preds.append(2)  # High
        return np.array(preds, dtype=int)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Produces synthetic probability simplex based on distance to decision thresholds.
        """
        probas = []
        for _, row in X.iterrows():
            score = self._compute_score(row)
            if score < 0.20:
                # Mostly Low
                p0 = 0.70 + (0.20 - score) * 1.5
                p1 = (1.0 - p0) * 0.7
                p2 = 1.0 - p0 - p1
            elif score < 0.50:
                # Mostly Medium
                p1 = 0.60
                dist_low = score - 0.20
                dist_high = 0.50 - score
                p0 = 0.25 if dist_low < dist_high else 0.15
                p2 = 1.0 - p1 - p0
            else:
                # Mostly High
                p2 = 0.70 + min(score - 0.50, 0.25)
                p1 = (1.0 - p2) * 0.7
                p0 = 1.0 - p2 - p1
            
            vec = np.array([p0, p1, p2])
            vec = np.maximum(vec, 0.001)
            vec = vec / vec.sum()
            probas.append(vec)
        return np.array(probas)
