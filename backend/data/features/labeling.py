"""
Ground-Truth Compliance Labeling System.

Computes transparent, objective compliance scores and target risk labels
evaluating vendor performance in the FUTURE target period (T_target).
Guarantees zero data leakage into historical feature vectors.
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from backend.data.schema import (
    Invoice, Filing, Reconciliation, GroundTruthLabel, RiskLabel, TWOPLACES
)


# Explicitly experimental ground-truth weights (NOT statutory penalties or official GST weights)
EXPERIMENTAL_GROUND_TRUTH_WEIGHTS = {
    "missing_gstr3b_penalty": 0.35,     # Severe: tax collected but not remitted
    "missing_gstr1_penalty": 0.20,      # Blocks buyer's ITC under s.16(2)(aa)
    "mismatch_rate_penalty": 0.20,      # Invoices with discrepancies
    "filing_delay_penalty": 0.10,       # Chronic delays past statutory deadline
    "duplicate_penalty": 0.10,          # Duplicate / fake ITC claims
    "missing_einvoice_penalty": 0.05,   # Regulatory e-invoice non-compliance
}

# Backward compatibility alias
DEFAULT_SCORING_WEIGHTS = EXPERIMENTAL_GROUND_TRUTH_WEIGHTS


class GroundTruthLabeler:
    """
    Calculates experimental ground-truth compliance outcomes on future evaluation periods.
    Weights are experimental research parameters for machine learning evaluation.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or EXPERIMENTAL_GROUND_TRUTH_WEIGHTS

    def evaluate_vendor_future_period(
        self,
        vendor_id: str,
        target_period: str,
        feature_end_period: str,
        target_invoices: List[Invoice],
        target_filings: List[Filing],
        target_reconciliations: List[Reconciliation]
    ) -> GroundTruthLabel:
        """
        Evaluates vendor compliance strictly in target_period.
        Produces composite score in [0.0, 1.0] where 1.0 is highest risk and 0.0 is zero risk.
        """
        # 1. Filings evaluation
        period_filings = [f for f in target_filings if f.vendor_id == vendor_id and f.tax_period == target_period]
        filing = period_filings[0] if period_filings else None

        missing_gstr3b = 1.0 if (filing and not filing.gstr3b_filed) else 0.0
        missing_gstr1 = 1.0 if (filing and not filing.gstr1_filed) else 0.0
        delay_days = filing.filing_delay_days if filing else 0
        # Normalize delay penalty: saturates at 30 days
        norm_delay = min(delay_days / 30.0, 1.0)

        # 2. Invoices & Reconciliations evaluation
        period_invs = [i for i in target_invoices if i.vendor_id == vendor_id and i.tax_period == target_period]
        period_recons = [r for r in target_reconciliations if r.vendor_id == vendor_id and r.tax_period == target_period]
        
        inv_count = len(period_invs)
        if inv_count > 0:
            mismatches = sum(1 for r in period_recons if r.reconciliation_status != "Matched")
            mismatch_rate = mismatches / inv_count
            duplicates = sum(1 for i in period_invs if i.is_duplicate)
            dup_rate = min(duplicates / inv_count, 1.0)
            missing_einv = sum(1 for r in period_recons if not r.einvoice_present)
            einv_rate = missing_einv / inv_count
        else:
            mismatch_rate = 0.0
            dup_rate = 0.0
            einv_rate = 0.0

        # Weighted risk score accumulation
        risk_score = (
            missing_gstr3b * self.weights["missing_gstr3b_penalty"]
            + missing_gstr1 * self.weights["missing_gstr1_penalty"]
            + mismatch_rate * self.weights["mismatch_rate_penalty"]
            + norm_delay * self.weights["filing_delay_penalty"]
            + dup_rate * self.weights["duplicate_penalty"]
            + einv_rate * self.weights["missing_einvoice_penalty"]
        )
        risk_score = min(max(round(risk_score, 4), 0.0), 1.0)

        # Experimental target classification cutoffs
        if risk_score >= 0.50:
            label = RiskLabel.HIGH
        elif risk_score >= 0.20:
            label = RiskLabel.MEDIUM
        else:
            label = RiskLabel.LOW

        factors = {
            "missing_gstr3b": missing_gstr3b,
            "missing_gstr1": missing_gstr1,
            "delay_days": float(delay_days),
            "mismatch_rate": round(mismatch_rate, 4),
            "duplicate_rate": round(dup_rate, 4),
            "missing_einvoice_rate": round(einv_rate, 4)
        }

        reasons = []
        if missing_gstr3b > 0:
            reasons.append("Defaulted on GSTR-3B tax payment")
        if missing_gstr1 > 0:
            reasons.append("Failed to file GSTR-1 sales return")
        if delay_days > 10:
            reasons.append(f"Filed returns {delay_days} days late")
        if mismatch_rate > 0.20:
            reasons.append(f"High invoice mismatch rate ({int(mismatch_rate*100)}%)")
        if dup_rate > 0:
            reasons.append("Submitted duplicate invoices for credit")
        if not reasons:
            reasons.append("Full statutory compliance with on-time filing")

        return GroundTruthLabel(
            vendor_id=vendor_id,
            feature_period_end=feature_end_period,
            target_period=target_period,
            raw_risk_score=risk_score,
            risk_label=label,
            risk_factors=factors,
            explanation="; ".join(reasons)
        )
