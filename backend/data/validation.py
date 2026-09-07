"""
Data Validation Engine for GST Transactions and Filings.

Enforces:
1. Invoice arithmetic consistency (paise precision)
2. Indian GST jurisdiction logic (Intra-state CGST+SGST vs Inter-state IGST)
3. Statutory GSTIN structure validation (2-digit state, 10-char PAN, 1 entity, 'Z', 1 checksum)
4. Temporal chronology (invoice date vs return filing date)
5. Duplicate invoice detection
"""

import re
from datetime import date
from decimal import Decimal
from typing import List, Dict, Any, Tuple, Optional
from backend.data.schema import Invoice, Vendor, Filing, SupplyType, TWOPLACES, Reconciliation


GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
STATE_CODE_MAP = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi",
    "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim",
    "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
    "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
    "24": "Gujarat", "27": "Maharashtra", "29": "Karnataka", "32": "Kerala",
    "33": "Tamil Nadu", "36": "Telangana", "37": "Andhra Pradesh"
}


class ValidationError(Exception):
    pass


def get_canonical_invoice_key(invoice: Invoice) -> Tuple[str, str, str]:
    """Returns vendor-scoped canonical identity: (vendor_id, invoice_number, financial_year)."""
    return (invoice.vendor_id, invoice.invoice_number, invoice.financial_year)


class DataValidator:
    """Automated integrity checks on canonical GST datasets."""

    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        self.tolerance = tolerance

    def validate_gstin(self, gstin: str) -> Tuple[bool, Optional[str]]:
        """Validate 15-character GSTIN structure."""
        if not gstin or not isinstance(gstin, str):
            return False, "GSTIN is missing or non-string"
        gstin = gstin.strip().upper()
        if len(gstin) != 15:
            return False, f"Invalid length {len(gstin)} (must be exactly 15 chars)"
        if not GSTIN_PATTERN.match(gstin):
            return False, f"GSTIN '{gstin}' does not match statutory format (2-digit state + 10-char PAN + 1 + Z + check)"
        state_code = gstin[:2]
        if state_code not in STATE_CODE_MAP:
            return False, f"Unknown state code '{state_code}' in GSTIN '{gstin}'"
        return True, None

    def validate_invoice_arithmetic(self, invoice: Invoice) -> List[str]:
        """Check total tax and invoice value arithmetic."""
        errors = []
        if invoice.taxable_value < Decimal("0.00"):
            errors.append(f"Negative taxable value: {invoice.taxable_value}")
        if invoice.cgst < Decimal("0.00") or invoice.sgst < Decimal("0.00") or invoice.igst < Decimal("0.00"):
            errors.append("Negative tax amount detected")

        computed_tax = (invoice.cgst + invoice.sgst + invoice.igst).quantize(TWOPLACES)
        if abs(invoice.total_tax - computed_tax) > self.tolerance:
            errors.append(
                f"Tax arithmetic mismatch: total_tax={invoice.total_tax} != (cgst={invoice.cgst} + sgst={invoice.sgst} + igst={invoice.igst} = {computed_tax})"
            )

        computed_invoice_value = (invoice.taxable_value + invoice.total_tax).quantize(TWOPLACES)
        if abs(invoice.invoice_value - computed_invoice_value) > self.tolerance:
            errors.append(
                f"Invoice value mismatch: invoice_value={invoice.invoice_value} != taxable({invoice.taxable_value}) + tax({invoice.total_tax}) = {computed_invoice_value}"
            )
        return errors

    def validate_gst_jurisdiction(self, invoice: Invoice, vendor_state: Optional[str] = None, buyer_state: Optional[str] = None) -> List[str]:
        """Verify intra-state vs inter-state tax routing."""
        errors = []
        if invoice.supply_type == SupplyType.INTRA_STATE:
            if invoice.igst > Decimal("0.00"):
                errors.append(f"INTRA_STATE supply cannot have IGST: {invoice.igst}")
            # Allow 1 paisa rounding difference for odd paise totals
            if abs(invoice.cgst - invoice.sgst) > Decimal("0.02"):
                errors.append(f"INTRA_STATE supply must have approximately equal CGST ({invoice.cgst}) and SGST ({invoice.sgst})")
        elif invoice.supply_type == SupplyType.INTER_STATE:
            if invoice.cgst > Decimal("0.00") or invoice.sgst > Decimal("0.00"):
                errors.append(f"INTER_STATE supply cannot have CGST ({invoice.cgst}) or SGST ({invoice.sgst})")

        # If both vendor and buyer states are known, verify supply_type consistency
        if vendor_state and buyer_state:
            is_same_state = vendor_state.strip().lower() == buyer_state.strip().lower()
            if is_same_state and invoice.supply_type != SupplyType.INTRA_STATE:
                errors.append(f"Same state '{vendor_state}' requires INTRA_STATE supply, got {invoice.supply_type}")
            elif not is_same_state and invoice.supply_type != SupplyType.INTER_STATE:
                errors.append(f"Different states ('{vendor_state}' vs '{buyer_state}') requires INTER_STATE supply, got {invoice.supply_type}")
        return errors

    def validate_temporal_consistency(self, invoice: Invoice, filing: Optional[Filing] = None) -> List[str]:
        """Verify dates and filing chronology."""
        errors = []
        # Check filing date is after invoice date
        if filing:
            if filing.gstr1_filing_date and filing.gstr1_filing_date < invoice.invoice_date:
                errors.append(f"GSTR-1 filing date ({filing.gstr1_filing_date}) cannot precede invoice date ({invoice.invoice_date})")
            if filing.gstr3b_filing_date and filing.gstr3b_filing_date < invoice.invoice_date:
                errors.append(f"GSTR-3B filing date ({filing.gstr3b_filing_date}) cannot precede invoice date ({invoice.invoice_date})")
        return errors

    def get_canonical_invoice_key(self, invoice: Invoice) -> Tuple[str, str, str]:
        """Returns vendor-scoped canonical identity: (vendor_id, invoice_number, financial_year)."""
        return (invoice.vendor_id, invoice.invoice_number, invoice.financial_year)



    def validate_itc_exposure(self, invoices: List[Invoice], reconciliations: List[Reconciliation]) -> List[str]:
        """Verify that discrepancy/ITC exposure does not exceed the total tax on the relevant invoice."""
        inv_map = {inv.invoice_id: inv for inv in invoices}
        errors = []
        for rec in reconciliations:
            inv = inv_map.get(rec.invoice_id)
            if inv:
                # Discrepancy amount cannot exceed total invoice tax (allowing 5 paise tolerance)
                if rec.discrepancy_amount > (inv.total_tax + self.tolerance):
                    errors.append(
                        f"ITC exposure ({rec.discrepancy_amount}) exceeds total tax ({inv.total_tax}) for invoice {rec.invoice_id}"
                    )
        return errors

    def check_duplicate_invoices(self, invoices: List[Invoice]) -> Dict[str, Any]:
        """
        Detects exact duplicates and groups them using vendor-scoped canonical identity:
        (vendor_id, invoice_number, financial_year).
        Differentiates intentional anomaly duplicates from accidental pipeline duplicates.
        """
        seen_keys = {}
        exact_duplicates = []
        intentional_duplicates = []
        
        for inv in invoices:
            # Vendor-scoped canonical identity: different vendors can legitimately use the same invoice_number
            key = (inv.vendor_id, inv.invoice_number, inv.financial_year)
            if key in seen_keys:
                if inv.is_duplicate or inv.anomaly_type in ("DUPLICATE_INVOICE", "NEAR_DUPLICATE_INVOICE"):
                    intentional_duplicates.append(inv.invoice_id)
                else:
                    exact_duplicates.append((seen_keys[key], inv.invoice_id))
            else:
                seen_keys[key] = inv.invoice_id
                
        return {
            "duplicate_count": len(exact_duplicates) + len(intentional_duplicates),
            "accidental_duplicates": exact_duplicates,
            "intentional_anomaly_duplicates": intentional_duplicates,
        }

    def validate_dataset(self, vendors: List[Vendor], invoices: List[Invoice], filings: List[Filing] = None, reconciliations: Optional[List[Reconciliation]] = None) -> Dict[str, Any]:
        """Run complete end-to-end validation suite on a generated or loaded dataset."""
        report = {
            "total_vendors": len(vendors),
            "total_invoices": len(invoices),
            "total_filings": len(filings) if filings else 0,
            "total_reconciliations": len(reconciliations) if reconciliations else 0,
            "vendor_errors": [],
            "invoice_arithmetic_errors": [],
            "jurisdiction_errors": [],
            "temporal_errors": [],
            "itc_exposure_errors": [],
            "duplicates": {},
            "valid_records_count": 0,
            "passed": False
        }

        # Validate vendors
        vendor_state_map = {}
        for v in vendors:
            is_valid_gstin, reason = self.validate_gstin(v.gstin)
            if not is_valid_gstin:
                report["vendor_errors"].append({"vendor_id": v.vendor_id, "error": reason})
            vendor_state_map[v.vendor_id] = v.state

        # Validate invoices
        filing_map = {(f.vendor_id, f.tax_period): f for f in (filings or [])}
        for inv in invoices:
            inv_errors = self.validate_invoice_arithmetic(inv)
            if inv_errors:
                report["invoice_arithmetic_errors"].append({"invoice_id": inv.invoice_id, "errors": inv_errors})

            v_state = vendor_state_map.get(inv.vendor_id)
            # Assuming buyer is TP001 in Karnataka (or default)
            jur_errors = self.validate_gst_jurisdiction(inv, vendor_state=v_state, buyer_state="Karnataka")
            if jur_errors:
                report["jurisdiction_errors"].append({"invoice_id": inv.invoice_id, "errors": jur_errors})

            f = filing_map.get((inv.vendor_id, inv.tax_period))
            temp_errors = self.validate_temporal_consistency(inv, f)
            if temp_errors:
                report["temporal_errors"].append({"invoice_id": inv.invoice_id, "errors": temp_errors})

        # ITC exposure validation
        if reconciliations:
            report["itc_exposure_errors"] = self.validate_itc_exposure(invoices, reconciliations)

        # Duplicates check
        report["duplicates"] = self.check_duplicate_invoices(invoices)

        total_errs = (
            len(report["vendor_errors"])
            + len(report["invoice_arithmetic_errors"])
            + len(report["jurisdiction_errors"])
            + len(report["temporal_errors"])
            + len(report["itc_exposure_errors"])
        )
        report["valid_records_count"] = len(invoices) - len(report["invoice_arithmetic_errors"])
        report["passed"] = (total_errs == 0) and (len(report["duplicates"]["accidental_duplicates"]) == 0)
        return report
