"""Tests for deterministic dataset reproducibility."""

from backend.data.synthetic.generator import SyntheticGSTDatasetGenerator


def test_seed_determinism():
    """Seed 42 twice must produce byte-for-byte identical vendor and invoice outputs."""
    gen1 = SyntheticGSTDatasetGenerator(seed=42)
    ds1 = gen1.generate_dataset(vendor_count=5, months_count=2)

    gen2 = SyntheticGSTDatasetGenerator(seed=42)
    ds2 = gen2.generate_dataset(vendor_count=5, months_count=2)

    # Identical vendor count and properties
    assert len(ds1["vendors"]) == len(ds2["vendors"])
    for v1, v2 in zip(ds1["vendors"], ds2["vendors"]):
        assert v1.vendor_id == v2.vendor_id
        assert v1.gstin == v2.gstin
        assert v1.state == v2.state
        assert v1.synthetic_profile == v2.synthetic_profile

    # Identical invoices count, values, and IDs
    assert len(ds1["invoices"]) == len(ds2["invoices"])
    for i1, i2 in zip(ds1["invoices"], ds2["invoices"]):
        assert i1.invoice_id == i2.invoice_id
        assert i1.taxable_value == i2.taxable_value
        assert i1.total_tax == i2.total_tax
        assert i1.invoice_value == i2.invoice_value
        assert i1.anomaly_type == i2.anomaly_type


def test_different_seeds_produce_different_data():
    gen1 = SyntheticGSTDatasetGenerator(seed=42)
    ds1 = gen1.generate_dataset(vendor_count=5, months_count=2)

    gen2 = SyntheticGSTDatasetGenerator(seed=999)
    ds2 = gen2.generate_dataset(vendor_count=5, months_count=2)

    invs1 = [i.invoice_value for i in ds1["invoices"]]
    invs2 = [i.invoice_value for i in ds2["invoices"]]
    assert invs1 != invs2
