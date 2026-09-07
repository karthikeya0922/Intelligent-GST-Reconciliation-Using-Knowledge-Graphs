"""
Data Preprocessing Pipeline for GST Risk Prediction.

Handles:
- Missing value imputation (median strategy)
- Feature scaling (StandardScaler for Logistic Regression; passthrough for tree models)
- Multiclass label encoding:
    0 = Low Risk
    1 = Medium Risk
    2 = High Risk
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


LABEL_TO_INT = {
    "Low": 0,
    "Medium": 1,
    "High": 2,
    # Also support uppercase
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2
}

INT_TO_LABEL = {
    0: "Low",
    1: "Medium",
    2: "High"
}

CLASS_NAMES = ["Low", "Medium", "High"]


def encode_labels(labels: pd.Series) -> np.ndarray:
    """Converts textual risk labels to integer classes (0, 1, 2)."""
    return labels.map(LABEL_TO_INT).to_numpy(dtype=int)


def decode_labels(int_labels: np.ndarray) -> List[str]:
    """Converts integer classes back to canonical title-case strings."""
    return [INT_TO_LABEL[int(i)] for i in int_labels]


def build_preprocessor(feature_columns: List[str], scale_features: bool = False) -> ColumnTransformer:
    """
    Constructs an sklearn ColumnTransformer fitted exclusively on training data.
    """
    if scale_features:
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ])
    else:
        pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median"))
        ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", pipeline, feature_columns)
        ],
        remainder="drop"
    )
    return preprocessor
