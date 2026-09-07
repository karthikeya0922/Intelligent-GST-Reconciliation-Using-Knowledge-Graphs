"""Tests for synthetic GST generator and behavioral profiles."""

import pytest
from backend.data.synthetic.generator import SyntheticGSTDatasetGenerator
from backend.data.synthetic.profiles import PROFILES


def test_synthetic_generator_output_structure():
    gen = SyntheticGSTDatasetGenerator(seed=42)
    data = gen.generate_dataset(vendor_count=20, months_count=12)

    assert len(data["vendors"]) == 20
    assert len(data["tax_periods"]) == 12
    assert len(data["invoices"]) > 0
    assert len(data["filings"]) == 20 * 12
    assert len(data["reconciliations"]) == len(data["invoices"])


def test_behavioral_profiles_present():
    gen = SyntheticGSTDatasetGenerator(seed=100)
    data = gen.generate_dataset(vendor_count=100, months_count=3)
    profiles = {v.synthetic_profile for v in data["vendors"]}
    
    # In 100 vendors with realistic distributions, major profiles A, B, C, D, E, F must appear
    for p in ["A", "B", "C", "D"]:
        assert p in profiles, f"Profile {p} missing from generated population"


def test_invoice_arithmetic_consistency():
    gen = SyntheticGSTDatasetGenerator(seed=42)
    data = gen.generate_dataset(vendor_count=10, months_count=2)
    
    for inv in data["invoices"]:
        # Pristine invoices (non-tax-mismatches) must strictly satisfy arithmetic
        if not inv.anomaly_type:
            assert inv.total_tax == inv.cgst + inv.sgst + inv.igst
            assert inv.invoice_value == inv.taxable_value + inv.total_tax
