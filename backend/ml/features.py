"""
Feature definitions and engineering for GST ITC risk prediction.

Organizes features into 4 statutory/commercial groups:
1. Transaction
2. Reconciliation
3. Compliance
4. ITC

Also provides derived historical features engineered strictly from information
available at or before prediction period T_k (zero future leakage).
"""

from typing import List, Dict, Any
import numpy as np
import pandas as pd


# 1. Primary Feature Groups from Phase 1.5 Canonical Schema
TRANSACTION_FEATURES = [
    "invoice_count",
    "total_invoice_value",
    "average_invoice_value",
    "total_tax"
]

RECONCILIATION_FEATURES = [
    "mismatch_count",
    "mismatch_rate",
    "duplicate_invoice_count",
    "missing_einvoice_count",
    "missing_eway_bill_count"
]

COMPLIANCE_FEATURES = [
    "missing_gstr1_count",
    "missing_gstr3b_count",
    "late_filing_count",
    "average_filing_delay"
]

ITC_FEATURES = [
    "itc_exposure"
]

HISTORICAL_STATE_FEATURES = [
    "previous_period_risk"
]

# Combined baseline tabular features
BASE_TABULAR_FEATURES = (
    TRANSACTION_FEATURES
    + RECONCILIATION_FEATURES
    + COMPLIANCE_FEATURES
    + ITC_FEATURES
    + HISTORICAL_STATE_FEATURES
)

# Derived feature names
DERIVED_TABULAR_FEATURES = [
    "itc_exposure_ratio",
    "tax_per_invoice",
    "unfiled_return_ratio",
    "mismatch_severity_index"
]

ALL_TABULAR_FEATURES = BASE_TABULAR_FEATURES + DERIVED_TABULAR_FEATURES


def engineer_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes derived historical features strictly from columns available at T_k.
    Guaranteed zero future data leakage.
    """
    out = df.copy()

    # Ensure required base columns exist with default 0.0
    for req_col in [
        "total_tax", "itc_exposure", "invoice_count", "missing_gstr1_count",
        "missing_gstr3b_count", "mismatch_rate", "duplicate_invoice_count"
    ]:
        if req_col not in out.columns:
            out[req_col] = 0.0

    # 1. ITC Exposure Ratio: Discrepancy exposure relative to total tax liability
    # Saturated between 0.0 and 1.0 to avoid division by zero or extreme outliers
    tax_denom = out["total_tax"].fillna(0.0) + 1.0
    out["itc_exposure_ratio"] = (out["itc_exposure"].fillna(0.0) / tax_denom).clip(lower=0.0, upper=1.0)

    # 2. Tax per Invoice: Average tax density per transaction
    inv_denom = out["invoice_count"].fillna(0.0).clip(lower=1.0)
    out["tax_per_invoice"] = out["total_tax"].fillna(0.0) / inv_denom

    # 3. Unfiled Return Ratio: Proportion of statutory filings missing in period (GSTR-1 + GSTR-3B out of 2)
    missing_returns = out["missing_gstr1_count"].fillna(0.0) + out["missing_gstr3b_count"].fillna(0.0)
    out["unfiled_return_ratio"] = (missing_returns / 2.0).clip(lower=0.0, upper=1.0)

    # 4. Mismatch Severity Index: Combined interaction of mismatch rate and duplicate attempts
    out["mismatch_severity_index"] = (
        out["mismatch_rate"].fillna(0.0) * 0.7 
        + (out["duplicate_invoice_count"].fillna(0.0).clip(upper=5.0) / 5.0) * 0.3
    ).clip(lower=0.0, upper=1.0)

    return out


def get_feature_group_columns(group_name: str) -> List[str]:
    """Returns column names for an experimental feature ablation group."""
    if group_name == "transaction":
        return list(TRANSACTION_FEATURES)
    elif group_name == "transaction_reconciliation":
        return list(TRANSACTION_FEATURES + RECONCILIATION_FEATURES)
    elif group_name == "transaction_reconciliation_compliance":
        return list(TRANSACTION_FEATURES + RECONCILIATION_FEATURES + COMPLIANCE_FEATURES)
    elif group_name == "all_tabular":
        return list(ALL_TABULAR_FEATURES)
    else:
        raise ValueError(f"Unknown feature group: {group_name}")
