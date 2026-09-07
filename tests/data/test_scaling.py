"""
Tests for dataset generator scaling capabilities.
"""
import pytest
from backend.data.synthetic.generator import SyntheticGSTGenerator

def test_scaling_generation_throughput():
    """Verify generator scales to 50 vendors and 12 months without errors."""
    gen = SyntheticGSTGenerator(seed=42)
    result = gen.generate_dataset(vendor_count=50, months_count=12)
    
    assert len(result["vendors"]) == 50
    assert len(result["tax_periods"]) == 12
    assert len(result["invoices"]) > 1000
    assert len(result["reconciliations"]) == len(result["invoices"])
    assert len(result["anomalies"]) > 50

def test_scaling_tax_periods():
    """Verify chronological sequence of generated tax periods."""
    gen = SyntheticGSTGenerator(seed=123)
    result = gen.generate_dataset(vendor_count=20, months_count=24)
    
    tax_periods = result["tax_periods"]
    assert len(tax_periods) == 24
    # Ensure periods are sorted chronologically
    sorted_periods = sorted(tax_periods)
    assert tax_periods == sorted_periods
