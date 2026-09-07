"""
Unit tests for Knowledge Graph Investigation Layer.
Verifies time-safe relationship extraction, counterparty concentration, and empty-graph handling.
"""

import pytest
from backend.ml.graph_investigation import GraphInvestigator


def test_graph_investigation_empty_handling():
    """Verifies clean, non-fabricated response when no graph edges exist for vendor."""
    inv = GraphInvestigator(sample_invoices=[])
    res = inv.investigate_vendor("NON_EXISTENT_VENDOR", "2026-03")

    assert res["supplier_count"] == 0
    assert res["customer_count"] == 0
    assert len(res["relationships"]) == 0
    assert "No meaningful graph relationships were available" in res["message"]


def test_graph_investigation_temporal_cutoff_enforcement():
    """Verifies invoices with tax_period > cutoff_period are strictly excluded from investigation."""
    sample_invoices = [
        # Past invoice (included in cutoff 2025-06)
        {"vendor_id": "V001", "buyer_id": "V002", "tax_period": "2025-05", "taxable_amount": 10000.0, "total_tax": 1800.0},
        {"vendor_id": "V003", "buyer_id": "V001", "tax_period": "2025-06", "taxable_amount": 20000.0, "total_tax": 3600.0},
        # Future invoice (must be excluded)
        {"vendor_id": "V004", "buyer_id": "V001", "tax_period": "2025-08", "taxable_amount": 90000.0, "total_tax": 16200.0}
    ]

    inv = GraphInvestigator(sample_invoices=sample_invoices)
    res = inv.investigate_vendor("V001", cutoff_period="2025-06")

    # Only V003 should be supplier at 2025-06; V004 is future and excluded!
    suppliers = [r["counterparty_id"] for r in res["relationships"] if "Supplier" in r["direction"]]
    assert "V003" in suppliers
    assert "V004" not in suppliers
    assert res["supplier_count"] == 1
    assert res["customer_count"] == 1


def test_reciprocal_bilateral_trade_flagging():
    """Verifies reciprocal bilateral trade (A -> B and B -> A) is detected and flagged."""
    sample_invoices = [
        {"vendor_id": "V001", "buyer_id": "V002", "tax_period": "2025-05", "taxable_amount": 50000.0, "total_tax": 9000.0},
        {"vendor_id": "V002", "buyer_id": "V001", "tax_period": "2025-05", "taxable_amount": 48000.0, "total_tax": 8640.0}
    ]

    inv = GraphInvestigator(sample_invoices=sample_invoices)
    res = inv.investigate_vendor("V001", cutoff_period="2025-05")

    assert res["reciprocal_count"] == 1
    flags = " ".join(res["network_flags"])
    assert "Reciprocal bilateral trading" in flags
    assert "V002" in flags
