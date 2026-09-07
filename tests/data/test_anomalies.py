"""Tests for anomaly injection engine."""

from datetime import date
from decimal import Decimal
import pytest

from backend.data.schema import Invoice, SupplyType, DataSource
from backend.data.synthetic.anomalies import AnomalyEngine, AnomalyType


@pytest.fixture
def sample_invoice():
    return Invoice(
        invoice_id="INV-TEST-001",
        vendor_id="V001",
        buyer_id="TP001",
        invoice_number="INV-2024-001",
        invoice_date=date(2024, 6, 15),
        financial_year="2024-25",
        tax_period="2024-06",
        taxable_value=Decimal("100000.00"),
        cgst=Decimal("9000.00"),
        sgst=Decimal("9000.00"),
        igst=Decimal("0.00"),
        total_tax=Decimal("18000.00"),
        invoice_value=Decimal("118000.00"),
        hsn_code="8471",
        supply_type=SupplyType.INTRA_STATE,
        data_source=DataSource.SYNTHETIC
    )


def test_tax_mismatch_injection(sample_invoice):
    engine = AnomalyEngine(seed=42)
    orig_tax = sample_invoice.total_tax
    anom_inv = engine.inject_tax_mismatch(sample_invoice, discrepancy_pct=0.20)
    
    assert anom_inv.anomaly_type == AnomalyType.TAX_MISMATCH.value
    assert anom_inv.total_tax != orig_tax
    assert len(engine.anomaly_log) == 1
    assert engine.anomaly_log[0].anomaly_type == AnomalyType.TAX_MISMATCH


def test_duplicate_invoice_injection(sample_invoice):
    engine = AnomalyEngine(seed=42)
    dup = engine.create_duplicate_invoice(sample_invoice, near_duplicate=False)
    
    assert dup.is_duplicate is True
    assert dup.anomaly_type == AnomalyType.DUPLICATE_INVOICE.value
    assert dup.invoice_id == f"{sample_invoice.invoice_id}-DUP"
    assert dup.invoice_number == sample_invoice.invoice_number


def test_near_duplicate_injection(sample_invoice):
    engine = AnomalyEngine(seed=42)
    near_dup = engine.create_duplicate_invoice(sample_invoice, near_duplicate=True)
    
    assert near_dup.is_duplicate is True
    assert near_dup.anomaly_type == AnomalyType.NEAR_DUPLICATE_INVOICE.value


def test_hsn_mismatch_injection(sample_invoice):
    engine = AnomalyEngine(seed=42)
    orig_hsn = sample_invoice.hsn_code
    anom_inv = engine.inject_hsn_mismatch(sample_invoice)
    
    assert anom_inv.hsn_code != orig_hsn
    assert anom_inv.anomaly_type == AnomalyType.HSN_MISMATCH.value
