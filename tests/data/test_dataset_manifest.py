"""
Tests for dataset manifest generation and metadata tracking.
"""
import pytest
import json
import os
from backend.data.manifest import create_dataset_manifest, generate_manifest_dict

def test_generate_manifest_dict():
    """Verify manifest dictionary structure and fields."""
    split_sizes = {
        "train_rows": 700,
        "validation_rows": 150,
        "test_rows": 150,
        "total_feature_rows": 1000
    }
    manifest = generate_manifest_dict(
        seed=42,
        vendor_count=100,
        invoice_count=5000,
        month_count=12,
        public_record_count=1000,
        synthetic_record_count=4000,
        split_sizes=split_sizes
    )
    
    assert manifest["dataset_version"] == "1.5.0"
    assert manifest["random_seed"] == 42
    assert manifest["parameters"]["vendor_count"] == 100
    assert manifest["parameters"]["months_count"] == 12
    assert manifest["record_counts"]["total_invoices"] == 5000
    assert manifest["record_counts"]["total_feature_rows"] == 1000
    assert "generation_timestamp" in manifest
    assert "schema_hashes" in manifest

def test_create_dataset_manifest_file(tmp_path):
    """Verify writing dataset manifest to file."""
    output_path = os.path.join(str(tmp_path), "dataset_manifest.json")
    split_sizes = {
        "train_rows": 50,
        "validation_rows": 10,
        "test_rows": 10,
        "total_feature_rows": 70
    }
    manifest = create_dataset_manifest(
        seed=101,
        vendor_count=20,
        invoice_count=200,
        month_count=6,
        public_record_count=0,
        synthetic_record_count=200,
        split_sizes=split_sizes,
        output_path=output_path
    )
    
    assert os.path.exists(output_path)
    with open(output_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["random_seed"] == 101
    assert loaded["dataset_version"] == "1.5.0"
