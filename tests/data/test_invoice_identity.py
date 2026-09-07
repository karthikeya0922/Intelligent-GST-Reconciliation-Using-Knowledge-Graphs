"""
Tests for vendor-scoped invoice identity and financial year boundaries.
"""
import pytest
from datetime import date
from decimal import Decimal
from backend.data.schema import Invoice, SupplyType, DataSource
from backend.data.validation import get_canonical_invoice_key, DataValidator

def create_sample_invoice(vendor_id: str, inv_num: str, inv_date: date, fin_year: str) -> Invoice:
    taxable = Decimal("1000.00")
    cgst = Decimal("90.00")
    sgst = Decimal("90.00")
    total = taxable + cgst + sgst
    
    return Invoice(
        invoice_id=f"{vendor_id}_{inv_num}_{fin_year}",
        vendor_id=vendor_id,
        buyer_id="TP001",
        vendor_gstin="27ABCDE1234F1Z5",
        buyer_gstin="27XYZAB5678C1Z2",
        invoice_number=inv_num,
        invoice_date=inv_date,
        financial_year=fin_year,
        tax_period=inv_date.strftime("%Y-%m"),
        taxable_value=taxable,
        cgst=cgst,
        sgst=sgst,
        igst=Decimal("0.00"),
        total_tax=cgst + sgst,
        invoice_value=total,
        hsn_code="9983",
        supply_type=SupplyType.INTRA_STATE,
        data_source=DataSource.SYNTHETIC,
        is_duplicate=False
    )

def test_canonical_invoice_key():
    """Verify get_canonical_invoice_key returns (vendor_id, invoice_number, financial_year)."""
    inv = create_sample_invoice("VEND_001", "INV-100", date(2023, 8, 15), "2023-24")
    key = get_canonical_invoice_key(inv)
    assert key == ("VEND_001", "INV-100", "2023-24")
    
    # Check January invoice belongs to FY 2023-24
    inv_jan = create_sample_invoice("VEND_001", "INV-101", date(2024, 1, 10), "2023-24")
    assert get_canonical_invoice_key(inv_jan) == ("VEND_001", "INV-101", "2023-24")
    
    # Check May 2024 invoice belongs to FY 2024-25
    inv_may = create_sample_invoice("VEND_001", "INV-100", date(2024, 5, 1), "2024-25")
    assert get_canonical_invoice_key(inv_may) == ("VEND_001", "INV-100", "2024-25")

def test_multi_vendor_same_invoice_number():
    """Verify different vendors having the same invoice number does NOT trigger duplicate detection."""
    inv_a = create_sample_invoice("VEND_001", "INV-001", date(2023, 7, 1), "2023-24")
    inv_b = create_sample_invoice("VEND_002", "INV-001", date(2023, 7, 1), "2023-24")
    
    validator = DataValidator()
    dups = validator.check_duplicate_invoices([inv_a, inv_b])
    assert len(dups["accidental_duplicates"]) == 0

def test_same_vendor_different_financial_years():
    """Verify same vendor issuing same invoice number in different financial years is allowed."""
    inv_fy1 = create_sample_invoice("VEND_001", "INV-001", date(2023, 5, 10), "2023-24")
    inv_fy2 = create_sample_invoice("VEND_001", "INV-001", date(2024, 5, 10), "2024-25")
    
    validator = DataValidator()
    dups = validator.check_duplicate_invoices([inv_fy1, inv_fy2])
    assert len(dups["accidental_duplicates"]) == 0

def test_same_vendor_same_fy_duplicate():
    """Verify same vendor issuing same invoice number in same financial year is caught as accidental duplicate."""
    inv1 = create_sample_invoice("VEND_001", "INV-001", date(2023, 5, 10), "2023-24")
    inv2 = create_sample_invoice("VEND_001", "INV-001", date(2023, 6, 15), "2023-24")
    
    validator = DataValidator()
    dups = validator.check_duplicate_invoices([inv1, inv2])
    assert len(dups["accidental_duplicates"]) == 1
