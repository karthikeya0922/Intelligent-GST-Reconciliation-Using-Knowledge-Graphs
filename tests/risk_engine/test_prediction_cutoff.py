"""
Unit tests for production prediction cutoff enforcement and audit logging.
Verifies temporal boundaries and audit log appending.
"""

import os
import json
import pytest
from backend.ml.risk_engine import ITCRiskEngine


def test_prediction_cutoff_assertion():
    """Verifies that submitting data timestamped > cutoff period raises ValueError."""
    engine = ITCRiskEngine()

    # Cutoff is 2025-06, but record is from 2025-07 (future lookahead)
    with pytest.raises(ValueError, match="Temporal Leakage Violation"):
        engine.assess_vendor(
            vendor_id="V001",
            period="2025-06",
            record={
                "vendor_id": "V001",
                "tax_period": "2025-07",
                "total_tax": 5000.0
            }
        )


def test_audit_log_generation(tmp_path):
    """Verifies each assessment writes an auditable entry with timestamp and parameters."""
    log_file = tmp_path / "test_audit.log"
    engine = ITCRiskEngine(audit_log_path=str(log_file))

    res = engine.assess_vendor("V001", "2026-03")
    assert os.path.exists(log_file)

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) >= 1
        entry = json.loads(lines[-1])
        assert entry["vendor_id"] == "V001"
        assert entry["prediction_period"] == "2026-03"
        assert "risk_score" in entry
        assert "model_version" in entry
        assert "timestamp" in entry
