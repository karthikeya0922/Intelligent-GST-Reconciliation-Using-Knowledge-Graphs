"""
Backward-Compatibility Bridge.

Maps the Phase 1 canonical GST models to the legacy dictionary representations
expected by existing FastAPI endpoints, MongoDB collections, and Neo4j graph projections.
Ensures zero breaking changes across existing views, API routes, and React UI components.
"""

from typing import List, Dict, Any, Optional
from backend.data.schema import Invoice, Vendor, Filing, Reconciliation


def canonical_vendor_to_legacy(vendor: Vendor, risk_score: float = 0.15) -> Dict[str, Any]:
    """Convert canonical Vendor model to legacy MongoDB schema."""
    if risk_score >= 0.60:
        status = "High Risk"
    elif risk_score >= 0.30:
        status = "Review"
    else:
        status = "Compliant"

    return {
        "id": vendor.vendor_id,
        "name": vendor.vendor_name,
        "gstin": vendor.gstin,
        "state": vendor.state,
        "riskScore": round(risk_score, 2),
        "status": status,
        "totalTransactions": 100,
        "missedFilings": 0,
        "avgDaysLate": 0,
        "businessCategory": vendor.business_category,
        "syntheticProfile": vendor.synthetic_profile
    }


def canonical_invoice_to_legacy(
    invoice: Invoice,
    vendor_name: str = "Unknown Supplier",
    reconciliation: Optional[Reconciliation] = None
) -> Dict[str, Any]:
    """Convert canonical Invoice model to legacy MongoDB schema."""
    gstr1_reported = True
    gstr2b_reported = True
    e_invoice = True
    e_waybill = True
    match_status = "Matched"
    risk_level = "Low"

    if reconciliation:
        gstr1_reported = reconciliation.gstr1_present
        gstr2b_reported = reconciliation.gstr2b_present
        e_invoice = reconciliation.einvoice_present
        e_waybill = reconciliation.ewaybill_present
        match_status = reconciliation.reconciliation_status.value if hasattr(reconciliation.reconciliation_status, "value") else str(reconciliation.reconciliation_status)

    if match_status != "Matched":
        risk_level = "High" if invoice.total_tax > 50000 else "Medium"

    return {
        "id": invoice.invoice_id,
        "vendorId": invoice.vendor_id,
        "vendorName": vendor_name,
        "gstin": invoice.vendor_gstin or "",
        "date": str(invoice.invoice_date),
        "taxableAmount": float(invoice.taxable_value),
        "cgst": float(invoice.cgst),
        "sgst": float(invoice.sgst),
        "igst": float(invoice.igst),
        "totalTax": float(invoice.total_tax),
        "total": float(invoice.invoice_value),
        "hsn": invoice.hsn_code,
        "period": invoice.tax_period,
        "gstr1Reported": gstr1_reported,
        "gstr2bReported": gstr2b_reported,
        "eInvoice": e_invoice,
        "eWayBill": e_waybill,
        "matchStatus": match_status,
        "riskLevel": risk_level,
        "inPurchaseRegister": reconciliation.purchase_register_present if reconciliation else True,
        "dataSource": invoice.data_source.value,
        "syntheticProfile": invoice.synthetic_profile,
        "anomalyType": invoice.anomaly_type
    }


def canonical_filing_to_legacy(filing: Filing, vendor_name: str = "Unknown Supplier", gstin: str = "") -> Dict[str, Any]:
    """Convert canonical Filing model to legacy returns collection record."""
    return {
        "gstin": gstin,
        "vendorId": filing.vendor_id,
        "vendorName": vendor_name,
        "type": "GSTR-3B",
        "period": filing.tax_period,
        "filed": filing.gstr3b_filed,
        "filedDate": str(filing.gstr3b_filing_date) if filing.gstr3b_filing_date else None,
        "status": "Filed" if filing.gstr3b_filed else "Not Filed",
    }
