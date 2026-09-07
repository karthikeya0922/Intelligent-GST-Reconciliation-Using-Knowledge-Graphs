"""
Data Normalization Module.

Sanitizes, coerces, and standardizes heterogeneous transaction inputs
(both raw external public records and synthetic records) into the canonical schema.
"""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
import re
from typing import Any, Optional, Dict, Union
from dateutil import parser as date_parser

from backend.data.schema import (
    Invoice, Vendor, SupplyType, DataSource, TWOPLACES, to_decimal_paise
)


# Standard Indian GST standard tax slabs: 0%, 5%, 12%, 18%, 28%
GST_TAX_SLABS = [
    Decimal("0.00"), Decimal("0.05"), Decimal("0.12"),
    Decimal("0.18"), Decimal("0.28")
]

# Canonical State normalization mapping
STATE_SYNONYMS = {
    "karnataka": "Karnataka",
    "ka": "Karnataka",
    "maharashtra": "Maharashtra",
    "mh": "Maharashtra",
    "gujarat": "Gujarat",
    "gujrat": "Gujarat",
    "gj": "Gujarat",
    "delhi": "Delhi",
    "dl": "Delhi",
    "tamil nadu": "Tamil Nadu",
    "tn": "Tamil Nadu",
    "telangana": "Telangana",
    "ts": "Telangana",
    "tg": "Telangana",
    "uttar pradesh": "Uttar Pradesh",
    "up": "Uttar Pradesh",
    "west bengal": "West Bengal",
    "wb": "West Bengal",
    "haryana": "Haryana",
    "hr": "Haryana",
}


def normalize_date(val: Any) -> date:
    """Safely parse arbitrary date formats into a standard date object."""
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if not val:
        return date.today()
    try:
        # dateutil parses ISO, US, UK, timestamp formats
        dt = date_parser.parse(str(val))
        return dt.date()
    except Exception:
        # Fallback to today if unparseable
        return date.today()


def normalize_state(val: Optional[str]) -> str:
    """Normalize state spelling and capitalizations."""
    if not val or not isinstance(val, str):
        return "Karnataka"
    clean = val.strip().lower()
    return STATE_SYNONYMS.get(clean, val.strip().title())


def normalize_hsn(val: Any) -> str:
    """Standardize HSN/SAC code to clean alphanumeric string."""
    if not val:
        return "9983"  # Default Other professional/technical services
    clean = re.sub(r"[^0-9A-Za-z]", "", str(val))
    if not clean:
        return "9983"
    return clean[:8]


def derive_financial_year(inv_date: date) -> str:
    """Indian financial year runs April 1 to March 31."""
    year = inv_date.year
    month = inv_date.month
    if month >= 4:
        return f"{year}-{str(year + 1)[-2:]}"
    else:
        return f"{year - 1}-{str(year)[-2:]}"


def derive_tax_period(inv_date: date) -> str:
    """Format filing period as YYYY-MM."""
    return inv_date.strftime("%Y-%m")


def normalize_tax_breakdown(
    taxable_val: Decimal,
    supply_type: SupplyType,
    total_tax: Optional[Decimal] = None,
    tax_rate: Optional[Decimal] = None
) -> Dict[str, Decimal]:
    """
    Ensures internal tax consistency according to Indian GST rules:
    - Intra-state: CGST = SGST = total_tax / 2, IGST = 0
    - Inter-state: IGST = total_tax, CGST = SGST = 0
    """
    taxable = taxable_val.quantize(TWOPLACES)
    
    # Determine total tax
    if total_tax is not None and total_tax > Decimal("0.00"):
        tax = total_tax.quantize(TWOPLACES)
    elif tax_rate is not None:
        tax = (taxable * tax_rate).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    else:
        # Default standard 18% slab
        tax = (taxable * Decimal("0.18")).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

    if supply_type == SupplyType.INTRA_STATE:
        half_tax = (tax / Decimal("2.00")).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
        cgst = half_tax
        # Account for potential 1 paisa rounding split
        sgst = tax - cgst
        igst = Decimal("0.00")
    else:
        cgst = Decimal("0.00")
        sgst = Decimal("0.00")
        igst = tax

    return {
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "total_tax": tax,
        "invoice_value": taxable + tax,
    }


def normalize_raw_invoice(
    raw_record: Dict[str, Any],
    vendor_state: str = "Karnataka",
    buyer_state: str = "Karnataka",
    source: DataSource = DataSource.PUBLIC
) -> Invoice:
    """
    Convert a generic raw dictionary into a validated canonical Invoice.
    """
    inv_date = normalize_date(raw_record.get("invoice_date") or raw_record.get("InvoiceDate") or raw_record.get("date"))
    raw_taxable = raw_record.get("taxable_value") or raw_record.get("taxableAmount") or raw_record.get("amount")
    
    # Handle price * quantity if taxable_value isn't explicitly provided
    if raw_taxable is None:
        qty = Decimal(str(raw_record.get("Quantity", 1)))
        price = to_decimal_paise(raw_record.get("UnitPrice", 0))
        taxable_val = abs(qty * price).quantize(TWOPLACES)
    else:
        taxable_val = abs(to_decimal_paise(raw_taxable))
    
    # Force minimal 100 paise if 0
    if taxable_val == Decimal("0.00"):
        taxable_val = Decimal("100.00")

    # Supply type based on state
    v_norm = normalize_state(vendor_state)
    b_norm = normalize_state(buyer_state)
    supply_type = SupplyType.INTRA_STATE if v_norm == b_norm else SupplyType.INTER_STATE
    
    # Breakdown
    raw_total_tax = raw_record.get("total_tax") or raw_record.get("totalTax") or raw_record.get("tax")
    tax_info = normalize_tax_breakdown(
        taxable_val=taxable_val,
        supply_type=supply_type,
        total_tax=to_decimal_paise(raw_total_tax) if raw_total_tax is not None else None
    )

    inv_id = str(raw_record.get("invoice_id") or raw_record.get("InvoiceNo") or raw_record.get("id") or "INV-RAW-001")
    inv_num = str(raw_record.get("invoice_number") or raw_record.get("InvoiceNo") or inv_id)

    return Invoice(
        invoice_id=inv_id,
        vendor_id=str(raw_record.get("vendor_id") or raw_record.get("vendorId") or "V-EXT-001"),
        buyer_id=str(raw_record.get("buyer_id") or "TP001"),
        vendor_gstin=raw_record.get("gstin") or raw_record.get("vendor_gstin"),
        buyer_gstin=raw_record.get("buyer_gstin") or "29AAQCQ1234M1Z8",
        invoice_number=inv_num,
        invoice_date=inv_date,
        financial_year=derive_financial_year(inv_date),
        tax_period=derive_tax_period(inv_date),
        taxable_value=taxable_val,
        cgst=tax_info["cgst"],
        sgst=tax_info["sgst"],
        igst=tax_info["igst"],
        total_tax=tax_info["total_tax"],
        invoice_value=tax_info["invoice_value"],
        hsn_code=normalize_hsn(raw_record.get("hsn_code") or raw_record.get("StockCode") or raw_record.get("hsn")),
        supply_type=supply_type,
        data_source=source,
        synthetic_profile=raw_record.get("synthetic_profile"),
        anomaly_type=raw_record.get("anomaly_type"),
        is_duplicate=bool(raw_record.get("is_duplicate", False))
    )
