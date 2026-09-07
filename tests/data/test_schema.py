"""Tests for canonical GST schema models and Decimal arithmetic."""

import pytest
from datetime import date
from decimal import Decimal
from pydantic import ValidationError

from backend.data.schema import (
    Vendor, Invoice, Filing, Reconciliation, SupplyType, DataSource, to_decimal_paise
)


def test_vendor_valid_creation():
    v = Vendor(
        vendor_id="V001",
        vendor_name="Tata Steel Ltd",
        gstin="29AABCU9603R1ZM",
        state="Karnataka",
        business_category="Steel & Metallurgy",
        registration_date=date(2018, 7, 1),
        is_active=True
    )
    assert v.vendor_id == "V001"
    assert v.state_code == "29"
    assert v.gstin == "29AABCU9603R1ZM"


def test_vendor_invalid_gstin_length():
    with pytest.raises(ValidationError):
        Vendor(
            vendor_id="V002",
            vendor_name="Invalid GSTIN Vendor",
            gstin="29AABCU9603R1Z",  # 14 chars
            state="Karnataka"
        )


def test_invoice_decimal_precision():
    inv = Invoice(
        invoice_id="INV-001",
        vendor_id="V001",
        buyer_id="TP001",
        invoice_number="INV-2024-001",
        invoice_date=date(2024, 7, 15),
        financial_year="2024-25",
        tax_period="2024-07",
        taxable_value="100000.50",
        cgst="9000.045",
        sgst="9000.045",
        igst="0.00",
        total_tax="18000.09",
        invoice_value="118000.59",
        hsn_code="7208",
        supply_type=SupplyType.INTRA_STATE,
        data_source=DataSource.SYNTHETIC
    )
    assert isinstance(inv.taxable_value, Decimal)
    assert isinstance(inv.total_tax, Decimal)
    assert inv.taxable_value == Decimal("100000.50")
    assert inv.total_tax == Decimal("18000.09")
    assert inv.invoice_value == Decimal("118000.59")


def test_invoice_rejects_negative_amounts():
    with pytest.raises(ValidationError):
        Invoice(
            invoice_id="INV-002",
            vendor_id="V001",
            buyer_id="TP001",
            invoice_number="INV-2024-002",
            invoice_date=date(2024, 7, 15),
            financial_year="2024-25",
            tax_period="2024-07",
            taxable_value="-5000.00",  # Negative
            cgst="0.00",
            sgst="0.00",
            igst="0.00",
            total_tax="0.00",
            invoice_value="0.00",
            hsn_code="9983",
            supply_type=SupplyType.INTRA_STATE
        )
