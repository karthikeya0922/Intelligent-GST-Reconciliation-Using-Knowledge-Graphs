"""Tests for data normalization and public data adapters."""

from datetime import date
from decimal import Decimal
from backend.data.normalization.normalize import (
    normalize_date, normalize_state, normalize_tax_breakdown, normalize_raw_invoice
)
from backend.data.schema import SupplyType, DataSource
from backend.data.public.adapters.retail_invoice import RetailInvoiceAdapter


def test_normalize_date():
    assert normalize_date("2024-07-15") == date(2024, 7, 15)
    assert normalize_date("15/07/2024") == date(2024, 7, 15)
    assert normalize_date("2024-07-15 14:30:00") == date(2024, 7, 15)


def test_normalize_state():
    assert normalize_state("karnataka") == "Karnataka"
    assert normalize_state("MH") == "Maharashtra"
    assert normalize_state("gujrat") == "Gujarat"


def test_normalize_tax_breakdown():
    # Intra-state 18% on 100,000
    tax_intra = normalize_tax_breakdown(
        taxable_val=Decimal("100000.00"),
        supply_type=SupplyType.INTRA_STATE,
        tax_rate=Decimal("0.18")
    )
    assert tax_intra["cgst"] == Decimal("9000.00")
    assert tax_intra["sgst"] == Decimal("9000.00")
    assert tax_intra["igst"] == Decimal("0.00")
    assert tax_intra["total_tax"] == Decimal("18000.00")
    assert tax_intra["invoice_value"] == Decimal("118000.00")

    # Inter-state 18% on 100,000
    tax_inter = normalize_tax_breakdown(
        taxable_val=Decimal("100000.00"),
        supply_type=SupplyType.INTER_STATE,
        tax_rate=Decimal("0.18")
    )
    assert tax_inter["cgst"] == Decimal("0.00")
    assert tax_inter["sgst"] == Decimal("0.00")
    assert tax_inter["igst"] == Decimal("18000.00")


def test_public_adapter_normalization():
    adapter = RetailInvoiceAdapter(seed=42)
    invoices = adapter.adapt_invoices(limit=10)
    assert len(invoices) > 0
    
    first = invoices[0]
    assert first.data_source == DataSource.PUBLIC
    assert isinstance(first.taxable_value, Decimal)
    assert first.total_tax == first.cgst + first.sgst + first.igst
