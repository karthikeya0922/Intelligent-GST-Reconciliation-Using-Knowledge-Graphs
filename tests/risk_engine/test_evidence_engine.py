"""
Unit tests for Evidence Engine.
Verifies multi-domain categorization, threshold evaluation, and evidence fidelity.
"""

import pytest
from backend.ml.evidence import EvidenceEngine


def test_evidence_categorization_and_thresholds():
    """Verifies evidence items are generated with correct domains, values, and severities."""
    engine = EvidenceEngine()

    sample_features = {
        "mismatch_rate": 0.28,
        "mismatch_count": 8,
        "duplicate_invoice_count": 2,
        "missing_gstr3b_count": 1,
        "average_filing_delay": 14.5,
        "total_tax": 80000.0,
        "itc_exposure": 120000.0,
        "itc_exposure_ratio": 0.35
    }

    evidence = engine.extract_evidence(sample_features)

    # 1. Domains check
    assert "reconciliation" in evidence
    assert "compliance" in evidence
    assert "transaction" in evidence
    assert "model" in evidence
    assert "graph" in evidence

    # 2. Reconciliation domain items
    recon_types = [item["feature"] for item in evidence["reconciliation"]]
    assert "mismatch_rate" in recon_types
    assert "mismatch_count" in recon_types
    assert "duplicate_invoice_count" in recon_types

    # Severity check: 28% mismatch rate is HIGH
    mm_item = next(item for item in evidence["reconciliation"] if item["feature"] == "mismatch_rate")
    assert mm_item["severity"] == "HIGH"
    assert mm_item["value"] == 0.28

    # 3. Compliance domain items
    comp_types = [item["feature"] for item in evidence["compliance"]]
    assert "missing_gstr3b_count" in comp_types
    assert "average_filing_delay" in comp_types

    delay_item = next(item for item in evidence["compliance"] if item["feature"] == "average_filing_delay")
    assert delay_item["severity"] == "HIGH"
    assert delay_item["value"] == 14.5


def test_clean_vendor_minimal_evidence():
    """Verifies compliant vendor produces no false high-severity flags."""
    engine = EvidenceEngine()

    clean_features = {
        "mismatch_rate": 0.01,
        "mismatch_count": 0,
        "duplicate_invoice_count": 0,
        "missing_gstr1_count": 0,
        "missing_gstr3b_count": 0,
        "average_filing_delay": 0.0,
        "itc_exposure": 0.0
    }

    evidence = engine.extract_evidence(clean_features)
    high_flags = [
        item for domain in evidence.values() for item in domain
        if item.get("severity") == "HIGH"
    ]
    assert len(high_flags) == 0
