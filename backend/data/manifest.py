"""
Dataset Manifest & Versioning Module.

Maintains formal provenance and reproducibility manifests for generated
hybrid GST datasets, ensuring Phase 2 ML experiments can cite precise versions.
"""

from datetime import datetime
import json
import os
from typing import Dict, Any, Optional


DATASET_VERSION = "1.5.0"
FEATURE_VERSION = "2.0"
LABEL_VERSION = "1.5-experimental"
GENERATOR_VERSION = "1.5.0-hybrid"


def generate_manifest_dict(
    seed: int,
    vendor_count: int,
    invoice_count: int,
    month_count: int,
    public_record_count: int,
    synthetic_record_count: int,
    split_sizes: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """Builds manifest dictionary with versioning, parameters, counts, and hashes."""
    splits = split_sizes or {}
    return {
        "dataset_version": DATASET_VERSION,
        "generation_timestamp": datetime.now().isoformat(),
        "random_seed": seed,
        "parameters": {
            "vendor_count": vendor_count,
            "months_count": month_count,
            "seed": seed
        },
        "record_counts": {
            "total_vendors": vendor_count,
            "total_invoices": invoice_count,
            "public_invoices": public_record_count,
            "synthetic_invoices": synthetic_record_count,
            "total_feature_rows": splits.get("total_feature_rows", 0)
        },
        "feature_version": FEATURE_VERSION,
        "label_version": LABEL_VERSION,
        "generator_version": GENERATOR_VERSION,
        "split_sizes": splits,
        "schema_hashes": {
            "invoice_schema": "pydantic-v2-canonical",
            "vendor_schema": "pydantic-v2-canonical",
            "feature_schema": "paise-decimal-v2"
        },
        "target_balance_spec": {
            "low_risk_target": "60-70%",
            "medium_risk_target": "20-25%",
            "high_risk_target": "10-15%",
            "disclaimer": "Experimental sampling configuration; not representative of statutory GST compliance prevalence."
        }
    }


def create_dataset_manifest(
    seed: int,
    vendor_count: int,
    invoice_count: int,
    month_count: int,
    public_record_count: int,
    synthetic_record_count: int,
    split_sizes: Optional[Dict[str, int]] = None,
    output_path: str = "data/reports/dataset_manifest.json"
) -> Dict[str, Any]:
    """Generates and writes dataset_manifest.json."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    manifest = generate_manifest_dict(
        seed=seed,
        vendor_count=vendor_count,
        invoice_count=invoice_count,
        month_count=month_count,
        public_record_count=public_record_count,
        synthetic_record_count=synthetic_record_count,
        split_sizes=split_sizes
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest

