"""
Evaluation and Metrics Engine for GST Risk Models.

Computes:
- Macro F1, Macro Recall, Balanced Accuracy
- Per-class Precision, Recall, F1
- Specific focus: High-Risk Recall, Precision, and F1
- Multiclass Confusion Matrix
- Log Loss & Multiclass Brier Score
- Error breakdown (False Low, False Medium, False High)
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    f1_score,
    recall_score,
    precision_score,
    balanced_accuracy_score,
    accuracy_score,
    confusion_matrix,
    log_loss
)


def compute_multiclass_brier_score(y_true: np.ndarray, y_prob: np.ndarray, n_classes: int = 3) -> float:
    """
    Computes standard multi-class Brier score:
    Brier = (1/N) * sum_i sum_c (p_ic - y_ic)^2
    """
    if y_prob is None or len(y_prob) == 0:
        return 0.0
    N = len(y_true)
    y_one_hot = np.zeros((N, n_classes))
    for i, label in enumerate(y_true):
        y_one_hot[i, int(label)] = 1.0
    brier = np.mean(np.sum((y_prob - y_one_hot) ** 2, axis=1))
    return float(brier)


def evaluate_model_performance(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Evaluates predictions against true ground-truth classes.
    """
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    macro_prec = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    acc = float(accuracy_score(y_true, y_pred))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    # Per-class scores: [Low (0), Medium (1), High (2)]
    precisions = precision_score(y_true, y_pred, average=None, labels=[0, 1, 2], zero_division=0)
    recalls = recall_score(y_true, y_pred, average=None, labels=[0, 1, 2], zero_division=0)
    f1s = f1_score(y_true, y_pred, average=None, labels=[0, 1, 2], zero_division=0)

    # Confusion matrix: [[C00, C01, C02], [C10, C11, C12], [C20, C21, C22]]
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist()

    # Probabilistic and calibration metrics
    loss_val = None
    brier_val = None
    if y_prob is not None:
        try:
            # Clip probabilities to prevent numerical underflow
            clipped_prob = np.clip(y_prob, 1e-15, 1.0 - 1e-15)
            clipped_prob = clipped_prob / clipped_prob.sum(axis=1, keepdims=True)
            loss_val = float(log_loss(y_true, clipped_prob, labels=[0, 1, 2]))
            brier_val = float(compute_multiclass_brier_score(y_true, clipped_prob, n_classes=3))
        except Exception:
            pass

    # Error analysis breakdown
    error_counts = {
        "actual_high_pred_low": int(cm[2][0]),     # Critical false low
        "actual_high_pred_medium": int(cm[2][1]),
        "actual_medium_pred_low": int(cm[1][0]),
        "actual_medium_pred_high": int(cm[1][2]),
        "actual_low_pred_medium": int(cm[0][1]),
        "actual_low_pred_high": int(cm[0][2]),      # False alarm
    }

    return {
        "macro_f1": round(macro_f1, 4),
        "macro_recall": round(macro_rec, 4),
        "macro_precision": round(macro_prec, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "accuracy": round(acc, 4),
        "weighted_f1": round(weighted_f1, 4),
        "class_metrics": {
            "Low": {
                "precision": round(float(precisions[0]), 4),
                "recall": round(float(recalls[0]), 4),
                "f1": round(float(f1s[0]), 4),
            },
            "Medium": {
                "precision": round(float(precisions[1]), 4),
                "recall": round(float(recalls[1]), 4),
                "f1": round(float(f1s[1]), 4),
            },
            "High": {
                "precision": round(float(precisions[2]), 4),
                "recall": round(float(recalls[2]), 4),
                "f1": round(float(f1s[2]), 4),
            }
        },
        "high_risk_metrics": {
            "recall": round(float(recalls[2]), 4),
            "precision": round(float(precisions[2]), 4),
            "f1": round(float(f1s[2]), 4),
        },
        "confusion_matrix": cm,
        "log_loss": round(loss_val, 4) if loss_val is not None else None,
        "brier_score": round(brier_val, 4) if brier_val is not None else None,
        "error_analysis": error_counts
    }
