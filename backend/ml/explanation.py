"""
Human-Readable Narrative Explanation Generator for GST Risk Engine.

Translates class-specific Tree SHAP attributions, financial ITC exposure, and evidence
into clear decision-support summaries with audit disclaimers.
"""

from typing import List, Dict, Any, Optional


class RiskExplanationGenerator:
    """Generates structured narrative explanations for vendor risk assessments."""

    FEATURE_FRIENDLY_NAMES = {
        "average_filing_delay": "statutory return filing delay",
        "mismatch_severity_index": "invoice reconciliation discrepancy severity",
        "late_filing_count": "repeated late return submissions",
        "previous_period_risk": "historical compliance risk rating",
        "unfiled_return_ratio": "unfiled GSTR statutory returns",
        "missing_einvoice_count": "invoices missing mandatory e-Invoice IRN",
        "missing_eway_bill_count": "consignments lacking mandatory e-Way Bills",
        "itc_exposure_ratio": "disputed ITC exposure relative to total tax",
        "mismatch_rate": "proportion of mismatched outward supply invoices",
        "itc_exposure": "monetary ITC exposure",
        "total_tax": "cumulative tax liability volume",
        "invoice_count": "transaction frequency"
    }

    def generate_explanation(
        self,
        vendor_id: str,
        prediction_period: str,
        model_class: str,
        risk_score: float,
        risk_band: str,
        itc_exposure: float,
        itc_exposure_ratio: float,
        top_factors: List[Dict[str, Any]],
        priority: str,
        recommended_action: str
    ) -> str:
        """Constructs a comprehensive, professional narrative risk summary."""
        friendly_factors = []
        for factor in top_factors[:4]:
            feat = factor.get("feature", "")
            name = self.FEATURE_FRIENDLY_NAMES.get(feat, feat.replace("_", " "))
            impact = factor.get("impact", "moderate")
            shap_val = factor.get("shap_value", 0.0)
            sign = "+" if shap_val >= 0 else ""
            friendly_factors.append(f"- {name} ({impact} impact, SHAP: {sign}{shap_val:.3f})")

        factors_text = "\n".join(friendly_factors) if friendly_factors else "- Standard commercial transaction patterns"

        narrative = (
            f"Vendor {vendor_id} is classified as {model_class} risk (Model Prediction) with an "
            f"ML Risk Indicator Score of {risk_score:.1f}/100 ({risk_band} Priority Band) for period {prediction_period}.\n\n"
            f"Key Model Risk Drivers (Tree SHAP):\n"
            f"{factors_text}\n\n"
            f"Financial ITC Exposure:\n"
            f"₹{itc_exposure:,.2f} ({itc_exposure_ratio:.1%} of invoiced tax liability currently at risk of clawback).\n\n"
            f"Operational Review Priority: {priority}.\n"
            f"Recommended Action: {recommended_action}\n\n"
            f"Disclaimer: This assessment is an automated machine-learning risk indicator designed solely for "
            f"audit prioritization and decision support. It does not constitute an official statutory GST tax assessment, "
            f"judicial determination of fraud, or legal finding of tax liability."
        )

        return narrative
