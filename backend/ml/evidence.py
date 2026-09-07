"""
Evidence Engine for GST Risk & Reconciliation System.

Translates raw transaction, reconciliation, compliance, model SHAP, and network
features into structured, auditable evidence items for decision support.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal


class EvidenceEngine:
    """Extracts structured evidence items across reconciliation, compliance, transaction, model, and graph domains."""

    # Documented domain thresholds based on statutory and Phase 1.5 reconciliation standards
    THRESHOLDS = {
        "mismatch_rate": {"medium": 0.05, "high": 0.20},
        "mismatch_count": {"medium": 1, "high": 5},
        "duplicate_invoice_count": {"high": 1},
        "missing_einvoice_count": {"high": 1},
        "missing_eway_bill_count": {"high": 1},
        "average_filing_delay": {"medium": 3.0, "high": 10.0},
        "late_filing_count": {"medium": 1, "high": 2},
        "missing_gstr1_count": {"high": 1},
        "missing_gstr3b_count": {"high": 1},
        "unfiled_return_ratio": {"medium": 0.25, "high": 0.50},
        "itc_exposure": {"medium": 25000.0, "high": 100000.0},
        "itc_exposure_ratio": {"medium": 0.05, "high": 0.25}
    }

    def __init__(self):
        pass

    def extract_evidence(
        self,
        features: Dict[str, Any],
        shap_factors: Optional[List[Dict[str, Any]]] = None,
        graph_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Builds categorized evidence dictionary:
        {
          "reconciliation": [...],
          "compliance": [...],
          "transaction": [...],
          "model": [...],
          "graph": [...]
        }
        """
        reconciliation_evidence = self._extract_reconciliation_evidence(features)
        compliance_evidence = self._extract_compliance_evidence(features)
        transaction_evidence = self._extract_transaction_evidence(features)
        model_evidence = self._extract_model_evidence(shap_factors or [])
        graph_evidence = self._extract_graph_evidence(graph_context or {})

        return {
            "reconciliation": reconciliation_evidence,
            "compliance": compliance_evidence,
            "transaction": transaction_evidence,
            "model": model_evidence,
            "graph": graph_evidence
        }

    def _extract_reconciliation_evidence(self, f: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = []

        # 1. Mismatch Rate
        rate = float(f.get("mismatch_rate", 0.0))
        if rate >= self.THRESHOLDS["mismatch_rate"]["high"]:
            items.append({
                "type": "RECONCILIATION",
                "feature": "mismatch_rate",
                "value": round(rate, 4),
                "severity": "HIGH",
                "description": f"Mismatch rate of {rate:.1%} exceeds high risk threshold (20.0%)."
            })
        elif rate >= self.THRESHOLDS["mismatch_rate"]["medium"]:
            items.append({
                "type": "RECONCILIATION",
                "feature": "mismatch_rate",
                "value": round(rate, 4),
                "severity": "MEDIUM",
                "description": f"Mismatch rate of {rate:.1%} warrants reconciliation review (>5.0%)."
            })

        # 2. Mismatch Count
        cnt = int(f.get("mismatch_count", 0))
        if cnt >= self.THRESHOLDS["mismatch_count"]["high"]:
            items.append({
                "type": "RECONCILIATION",
                "feature": "mismatch_count",
                "value": cnt,
                "severity": "HIGH",
                "description": f"{cnt} invoices flagged with reconciliation discrepancies in outward supply."
            })
        elif cnt > 0:
            items.append({
                "type": "RECONCILIATION",
                "feature": "mismatch_count",
                "value": cnt,
                "severity": "MEDIUM",
                "description": f"{cnt} invoice discrepancy observed in period."
            })

        # 3. Duplicate Invoices
        dups = int(f.get("duplicate_invoice_count", 0))
        if dups > 0:
            items.append({
                "type": "RECONCILIATION",
                "feature": "duplicate_invoice_count",
                "value": dups,
                "severity": "HIGH",
                "description": f"{dups} duplicate invoice number attempt(s) detected across reporting periods."
            })

        # 4. Missing e-Invoices (IRN)
        missing_einv = int(f.get("missing_einvoice_count", 0))
        if missing_einv > 0:
            items.append({
                "type": "RECONCILIATION",
                "feature": "missing_einvoice_count",
                "value": missing_einv,
                "severity": "HIGH",
                "description": f"{missing_einv} invoice(s) exceed statutory threshold without mandatory Invoice Reference Number (IRN)."
            })

        # 5. Missing e-Way Bills
        missing_ewb = int(f.get("missing_eway_bill_count", 0))
        if missing_ewb > 0:
            items.append({
                "type": "RECONCILIATION",
                "feature": "missing_eway_bill_count",
                "value": missing_ewb,
                "severity": "HIGH",
                "description": f"{missing_ewb} consignment(s) > ₹50,000 lack mandatory e-Way Bill documentation."
            })

        return items

    def _extract_compliance_evidence(self, f: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = []

        # 1. Missing GSTR-1
        gstr1 = int(f.get("missing_gstr1_count", 0))
        if gstr1 > 0:
            items.append({
                "type": "COMPLIANCE",
                "feature": "missing_gstr1_count",
                "value": gstr1,
                "severity": "HIGH",
                "description": "Vendor omitted mandatory outward return (GSTR-1), blocking buyer auto-population in GSTR-2B."
            })

        # 2. Missing GSTR-3B
        gstr3b = int(f.get("missing_gstr3b_count", 0))
        if gstr3b > 0:
            items.append({
                "type": "COMPLIANCE",
                "feature": "missing_gstr3b_count",
                "value": gstr3b,
                "severity": "HIGH",
                "description": "Vendor omitted summary tax payment return (GSTR-3B); tax collected has not been remitted to government."
            })

        # 3. Filing Delay
        delay = float(f.get("average_filing_delay", 0.0))
        if delay >= self.THRESHOLDS["average_filing_delay"]["high"]:
            items.append({
                "type": "COMPLIANCE",
                "feature": "average_filing_delay",
                "value": round(delay, 1),
                "severity": "HIGH",
                "description": f"Chronic filing delay averaging {delay:.1f} days past the statutory due date."
            })
        elif delay >= self.THRESHOLDS["average_filing_delay"]["medium"]:
            items.append({
                "type": "COMPLIANCE",
                "feature": "average_filing_delay",
                "value": round(delay, 1),
                "severity": "MEDIUM",
                "description": f"Minor filing delay averaging {delay:.1f} days past the statutory due date."
            })

        # 4. Late Filing Count
        late_cnt = int(f.get("late_filing_count", 0))
        if late_cnt >= self.THRESHOLDS["late_filing_count"]["high"]:
            items.append({
                "type": "COMPLIANCE",
                "feature": "late_filing_count",
                "value": late_cnt,
                "severity": "HIGH",
                "description": f"Multiple repeated late submissions ({late_cnt} instances) logged."
            })

        return items

    def _extract_transaction_evidence(self, f: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = []

        # 1. Total Tax & Volume
        inv_cnt = int(f.get("invoice_count", 0))
        tot_tax = float(f.get("total_tax", 0.0))
        items.append({
            "type": "TRANSACTION",
            "feature": "transaction_volume",
            "value": inv_cnt,
            "severity": "INFORMATIONAL",
            "description": f"Commercial activity: {inv_cnt} B2B invoices with ₹{tot_tax:,.2f} total invoiced tax."
        })

        # 2. ITC Exposure Quantum
        itc_exp = float(f.get("itc_exposure", 0.0))
        if itc_exp >= self.THRESHOLDS["itc_exposure"]["high"]:
            items.append({
                "type": "TRANSACTION",
                "feature": "itc_exposure",
                "value": round(itc_exp, 2),
                "severity": "HIGH",
                "description": f"Substantial ITC exposure of ₹{itc_exp:,.2f} at risk of tax authority clawback."
            })
        elif itc_exp >= self.THRESHOLDS["itc_exposure"]["medium"]:
            items.append({
                "type": "TRANSACTION",
                "feature": "itc_exposure",
                "value": round(itc_exp, 2),
                "severity": "MEDIUM",
                "description": f"Moderate ITC exposure of ₹{itc_exp:,.2f} associated with pending reconciliations."
            })

        # 3. ITC Exposure Ratio
        itc_ratio = float(f.get("itc_exposure_ratio", 0.0))
        if itc_ratio >= self.THRESHOLDS["itc_exposure_ratio"]["high"]:
            items.append({
                "type": "TRANSACTION",
                "feature": "itc_exposure_ratio",
                "value": round(itc_ratio, 4),
                "severity": "HIGH",
                "description": f"{itc_ratio:.1%} of invoiced tax is contested or at risk."
            })

        return items

    def _extract_model_evidence(self, shap_factors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        items = []
        for factor in shap_factors[:4]:
            feat = factor.get("feature", "unknown")
            shap_val = factor.get("shap_value", 0.0)
            direction = factor.get("direction", "increases_risk")
            val = factor.get("value")

            desc = f"Model Tree SHAP attribution: '{feat}' (val={val}) {direction} with impact +{abs(shap_val):.4f}."
            items.append({
                "type": "MODEL",
                "feature": feat,
                "value": val,
                "severity": "HIGH" if abs(shap_val) > 0.15 else "MEDIUM",
                "description": desc
            })
        return items

    def _extract_graph_evidence(self, g: Dict[str, Any]) -> List[Dict[str, Any]]:
        items = []
        sup_cnt = g.get("supplier_count", 0)
        cust_cnt = g.get("customer_count", 0)

        if sup_cnt > 0 or cust_cnt > 0:
            items.append({
                "type": "GRAPH",
                "feature": "network_connectivity",
                "value": {"suppliers": sup_cnt, "customers": cust_cnt},
                "severity": "INFORMATIONAL",
                "description": f"Trading network: {sup_cnt} upstream suppliers, {cust_cnt} downstream buyers identified."
            })

        flags = g.get("network_flags", [])
        for flag in flags:
            items.append({
                "type": "GRAPH",
                "feature": "network_flag",
                "value": flag,
                "severity": "HIGH" if "reciprocal" in flag.lower() or "cycle" in flag.lower() else "MEDIUM",
                "description": f"Network structural signal: {flag}"
            })

        return items
