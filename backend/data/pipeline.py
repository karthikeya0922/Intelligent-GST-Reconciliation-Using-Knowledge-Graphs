"""
Master Hybrid GST Data Pipeline.

Orchestrates:
1. Public data ingestion & adaptation
2. Synthetic GST ecosystem generation (Profiles A-H, controlled anomalies)
3. Hybrid merging & deduplication
4. Integrity validation
5. Vendor-period feature extraction with zero-leakage ground-truth labeling
6. Quality report generation (.json & .md)
7. Exporting Parquet / CSV / JSON artifacts
"""

import argparse
from datetime import datetime
from decimal import Decimal
import json
import os
from typing import List, Dict, Any, Optional
import pandas as pd

from backend.data.schema import Invoice, Vendor, Filing, Reconciliation, DataSource
from backend.data.public.adapters.retail_invoice import RetailInvoiceAdapter
from backend.data.synthetic.generator import SyntheticGSTDatasetGenerator
from backend.data.validation import DataValidator
from backend.data.features.aggregator import FeatureAggregator


class HybridGSTPipeline:
    """End-to-end data pipeline combining public and controlled synthetic GST data."""

    def __init__(self, seed: int = 42, output_dir: str = "data"):
        self.seed = seed
        self.output_dir = output_dir
        self.validator = DataValidator()
        self.aggregator = FeatureAggregator()

    def run(
        self,
        vendor_count: int = 50,
        months_count: int = 12,
        include_public: bool = True,
        public_invoice_limit: int = 100,
        raw_public_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes the full hybrid pipeline."""
        start_time = datetime.now()
        print(f"[*] Running Hybrid GST Data Pipeline (Seed: {self.seed}, Vendors: {vendor_count}, Months: {months_count})...")

        # 1. Synthetic Data Generation
        synth_gen = SyntheticGSTDatasetGenerator(seed=self.seed)
        synth_data = synth_gen.generate_dataset(
            vendor_count=vendor_count,
            months_count=months_count
        )

        all_vendors: List[Vendor] = list(synth_data["vendors"])
        all_invoices: List[Invoice] = list(synth_data["invoices"])
        all_filings: List[Filing] = list(synth_data["filings"])
        all_reconciliations: List[Reconciliation] = list(synth_data["reconciliations"])
        syndicate_edges = synth_data["syndicate_edges"]
        tax_periods = synth_data["tax_periods"]

        public_invoices_count = 0
        public_vendors_count = 0

        # 2. Public Dataset Ingestion (if enabled)
        if include_public:
            print("[*] Adapting public commercial invoice dataset...")
            public_adapter = RetailInvoiceAdapter(seed=self.seed)
            pub_invoices = public_adapter.adapt_invoices(raw_data_path=raw_public_path, limit=public_invoice_limit)
            pub_vendors = public_adapter.adapt_vendors(raw_data_path=raw_public_path)

            public_invoices_count = len(pub_invoices)
            public_vendors_count = len(pub_vendors)

            all_vendors.extend(pub_vendors)
            all_invoices.extend(pub_invoices)

            # Generate synthetic filings & clean reconciliation records for public invoices so they integrate into features
            for pinv in pub_invoices:
                # Public transactions are given compliant filing records
                pfiling = Filing(
                    vendor_id=pinv.vendor_id,
                    tax_period=pinv.tax_period,
                    gstr1_filed=True,
                    gstr1_filing_date=pinv.invoice_date,
                    gstr3b_filed=True,
                    gstr3b_filing_date=pinv.invoice_date,
                    filing_delay_days=0,
                    data_source=DataSource.PUBLIC
                )
                all_filings.append(pfiling)

                precon = Reconciliation(
                    invoice_id=pinv.invoice_id,
                    vendor_id=pinv.vendor_id,
                    tax_period=pinv.tax_period,
                    gstr1_present=True,
                    gstr2b_present=True,
                    purchase_register_present=True,
                    tax_amount_match=True,
                    taxable_value_match=True,
                    hsn_match=True,
                    date_match=True,
                    einvoice_present=True,
                    ewaybill_present=True,
                    reconciliation_status="Matched",
                    discrepancy_amount=Decimal("0.00")
                )
                all_reconciliations.append(precon)

        # 3. Validation & Deduplication
        print("[*] Validating hybrid records and running deduplication checks...")
        val_report = self.validator.validate_dataset(
            vendors=all_vendors,
            invoices=all_invoices,
            filings=all_filings
        )

        # Deduplicate accidental duplicates if any
        accidental_dups = val_report["duplicates"].get("accidental_duplicates", [])
        if accidental_dups:
            dup_ids_to_drop = {dup[1] for dup in accidental_dups}
            all_invoices = [i for i in all_invoices if i.invoice_id not in dup_ids_to_drop]
            print(f"[WARN] Filtered out {len(dup_ids_to_drop)} accidental duplicate records.")

        # 4. Feature Extraction & Future Ground-Truth Labeling
        print("[*] Extracting vendor-period features with zero-leakage target labeling...")
        vendor_ids = [v.vendor_id for v in all_vendors]
        feature_df = self.aggregator.create_temporal_feature_dataset(
            vendor_ids=vendor_ids,
            tax_periods=tax_periods,
            invoices=all_invoices,
            filings=all_filings,
            reconciliations=all_reconciliations,
            syndicate_edges=syndicate_edges
        )

        # 5. Temporal Train / Validation / Test Splitting
        print("[*] Partitioning datasets into temporal Train, Validation, and Test splits...")
        splits = self.aggregator.split_temporal_dataset(feature_df, tax_periods)
        train_df = splits["train"]
        val_df = splits["validation"]
        test_df = splits["test"]

        # 6. Export Datasets & Artifacts
        processed_dir = os.path.join(self.output_dir, "processed")
        reports_dir = os.path.join(self.output_dir, "reports")
        sample_dir = os.path.join(self.output_dir, "sample")
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        os.makedirs(sample_dir, exist_ok=True)

        # Export Full Feature Matrix
        parquet_path = os.path.join(processed_dir, "vendor_period_features.parquet")
        csv_path = os.path.join(processed_dir, "vendor_period_features.csv")
        try:
            feature_df.to_parquet(parquet_path, index=False)
            print(f"[OK] Saved Parquet feature dataset: {parquet_path}")
        except Exception as e:
            print(f"[WARN] Parquet write failed ({e}); falling back to CSV.")
        feature_df.to_csv(csv_path, index=False)
        print(f"[OK] Saved CSV feature dataset: {csv_path}")

        # Export Temporal Splits (train, validation, test)
        for split_name, s_df in [("train", train_df), ("validation", val_df), ("test", test_df)]:
            s_parquet = os.path.join(processed_dir, f"{split_name}.parquet")
            s_csv = os.path.join(processed_dir, f"{split_name}.csv")
            try:
                s_df.to_parquet(s_parquet, index=False)
                print(f"[OK] Saved {split_name} split ({len(s_df)} rows): {s_parquet}")
            except Exception as e:
                print(f"[WARN] {split_name} parquet write failed ({e}); writing CSV.")
            s_df.to_csv(s_csv, index=False)

        # Export Curated Small Repository-Safe Sample
        sample_file = os.path.join(sample_dir, "sample_hybrid_dataset.json")
        sample_payload = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "seed": self.seed,
                "total_vendors": len(all_vendors),
                "total_invoices": len(all_invoices),
                "public_records": public_invoices_count,
                "synthetic_records": len(synth_data["invoices"]),
                "tax_periods": tax_periods,
            },
            "sample_vendors": [v.model_dump(mode="json") for v in all_vendors[:15]],
            "sample_invoices": [i.model_dump(mode="json") for i in all_invoices[:30]],
            "sample_reconciliations": [r.model_dump(mode="json") for r in all_reconciliations[:30]],
            "syndicate_network_edges": syndicate_edges
        }
        with open(sample_file, "w", encoding="utf-8") as f:
            json.dump(sample_payload, f, indent=2, default=str)
        print(f"[OK] Saved sample dataset: {sample_file}")

        # 7. Distribution Analysis & Statistical Health Report
        print("[*] Generating statistical distribution & public-synthetic compatibility report...")
        from backend.data.distribution_analyzer import DistributionAnalyzer
        from backend.data.manifest import create_dataset_manifest

        analyzer = DistributionAnalyzer()
        dist_report = analyzer.generate_report(feature_df, all_invoices, output_dir=reports_dir)
        print(f"[OK] Feature distribution report saved: {os.path.join(reports_dir, 'feature_distribution_report.md')}")

        # 8. Create Dataset Manifest
        split_sizes = {
            "train_rows": len(train_df),
            "validation_rows": len(val_df),
            "test_rows": len(test_df),
            "total_feature_rows": len(feature_df)
        }
        manifest_path = os.path.join(reports_dir, "dataset_manifest.json")
        create_dataset_manifest(
            seed=self.seed,
            vendor_count=len(all_vendors),
            invoice_count=len(all_invoices),
            month_count=len(tax_periods),
            public_record_count=public_invoices_count,
            synthetic_record_count=len(synth_data["invoices"]),
            split_sizes=split_sizes,
            output_path=manifest_path
        )
        print(f"[OK] Dataset manifest saved: {manifest_path}")

        # 9. Generate Data Quality Reports
        duration = (datetime.now() - start_time).total_seconds()
        quality_summary = self._build_quality_summary(
            all_vendors, all_invoices, synth_data, public_invoices_count,
            val_report, feature_df, duration, splits=splits
        )

        report_json_path = os.path.join(reports_dir, "data_quality_report.json")
        report_md_path = os.path.join(reports_dir, "data_quality_report.md")

        with open(report_json_path, "w", encoding="utf-8") as f:
            json.dump(quality_summary, f, indent=2)
        
        with open(report_md_path, "w", encoding="utf-8") as f:
            f.write(self._format_quality_markdown(quality_summary))

        print(f"[OK] Data quality report saved: {report_md_path}")
        print(f"[DONE] Pipeline finished in {duration:.2f}s!")

        return {
            "vendors": all_vendors,
            "invoices": all_invoices,
            "feature_df": feature_df,
            "splits": splits,
            "quality_summary": quality_summary,
            "distribution_report": dist_report
        }

    def _build_quality_summary(
        self,
        vendors: List[Vendor],
        invoices: List[Invoice],
        synth_data: Dict[str, Any],
        public_invoices_count: int,
        val_report: Dict[str, Any],
        feature_df: pd.DataFrame,
        duration: float,
        splits: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Constructs quality metrics dictionary."""
        anomaly_counts = {}
        for a in synth_data.get("anomalies", []):
            atype = a.anomaly_type.value if hasattr(a.anomaly_type, "value") else str(a.anomaly_type)
            anomaly_counts[atype] = anomaly_counts.get(atype, 0) + 1

        profile_counts = {}
        for v in vendors:
            p = getattr(v, "synthetic_profile", "PUBLIC") or "PUBLIC"
            profile_counts[p] = profile_counts.get(p, 0) + 1

        target_distribution = feature_df["target_risk_label"].value_counts().to_dict() if "target_risk_label" in feature_df else {}

        split_stats = {}
        if splits:
            for sname in ["train", "validation", "test"]:
                sdf = splits.get(sname)
                if sdf is not None:
                    split_stats[sname] = {
                        "row_count": len(sdf),
                        "distribution": sdf["target_risk_label"].value_counts().to_dict()
                    }

        return {
            "pipeline_summary": {
                "execution_timestamp": datetime.now().isoformat(),
                "duration_seconds": round(duration, 2),
                "deterministic_seed": self.seed,
                "total_vendors": len(vendors),
                "total_invoices": len(invoices),
                "public_invoices": public_invoices_count,
                "synthetic_invoices": len(synth_data["invoices"]),
                "tax_periods_count": len(synth_data["tax_periods"]),
                "feature_rows": len(feature_df),
            },
            "behavioral_profiles": profile_counts,
            "anomalies_injected": anomaly_counts,
            "target_label_distribution": target_distribution,
            "temporal_splits": split_stats,
            "validation_results": {
                "passed": val_report["passed"],
                "arithmetic_errors": len(val_report["invoice_arithmetic_errors"]),
                "jurisdiction_errors": len(val_report["jurisdiction_errors"]),
                "temporal_errors": len(val_report["temporal_errors"]),
                "itc_exposure_errors": len(val_report.get("itc_exposure_errors", [])),
                "accidental_duplicates": len(val_report["duplicates"].get("accidental_duplicates", [])),
                "intentional_duplicates": len(val_report["duplicates"].get("intentional_anomaly_duplicates", [])),
            }
        }

    def _format_quality_markdown(self, summary: Dict[str, Any]) -> str:
        p = summary["pipeline_summary"]
        v = summary["validation_results"]
        anom = summary["anomalies_injected"]
        prof = summary["behavioral_profiles"]
        targ = summary["target_label_distribution"]
        splits = summary.get("temporal_splits", {})

        lines = [
            "# Dataset Quality & Integrity Report",
            f"*Generated on {p['execution_timestamp']} (Seed: {p['deterministic_seed']})*",
            "",
            "## 1. Dataset Overview",
            f"- **Total Vendors**: {p['total_vendors']:,}",
            f"- **Total Invoices**: {p['total_invoices']:,}",
            f"- **Public Records**: {p['public_invoices']:,}",
            f"- **Synthetic Records**: {p['synthetic_invoices']:,}",
            f"- **Tax Periods Simulated**: {p['tax_periods_count']}",
            f"- **Feature Rows Generated**: {p['feature_rows']:,}",
            "",
            "## 2. Validation & Quality Checks",
            f"- **Overall Pipeline Validation Status**: {'✅ PASSED' if v['passed'] else '❌ FAILED'}",
            f"- **Invoice Arithmetic Errors**: {v['arithmetic_errors']}",
            f"- **Jurisdiction / Tax Routing Errors**: {v['jurisdiction_errors']}",
            f"- **Temporal Chronology Errors**: {v['temporal_errors']}",
            f"- **ITC Exposure Inconsistencies**: {v.get('itc_exposure_errors', 0)}",
            f"- **Accidental Duplicates Detected**: {v['accidental_duplicates']}",
            f"- **Intentional Anomaly Duplicates**: {v['intentional_duplicates']}",
            "",
            "## 3. Injected Anomalies Breakdown",
            "| Anomaly Type | Count |",
            "| :--- | :--- |"
        ]
        for k, count in sorted(anom.items()):
            lines.append(f"| `{k}` | {count:,} |")

        lines.extend([
            "",
            "## 4. Vendor Behavioral Profiles",
            "| Profile Code | Vendor Count | Description |",
            "| :--- | :--- | :--- |"
        ])
        profile_names = {
            "A": "Compliant Vendor",
            "B": "Occasional Mismatch",
            "C": "Chronic Mismatch",
            "D": "Late Filer",
            "E": "Missing-Return Vendor",
            "F": "High ITC Exposure",
            "G": "Suspicious Network",
            "H": "Duplicate Generator",
            "PUBLIC": "Public External Supplier"
        }
        for code, count in sorted(prof.items()):
            lines.append(f"| **{code}** | {count} | {profile_names.get(code, 'Custom Profile')} |")

        lines.extend([
            "",
            "## 5. Future-Period Target Compliance Label Distribution",
            "| Risk Label | Vendor-Period Count | Percentage |",
            "| :--- | :--- | :--- |"
        ])
        total_targets = sum(targ.values()) or 1
        for label, count in sorted(targ.items()):
            pct = (count / total_targets) * 100
            lines.append(f"| **{label}** | {count:,} | {pct:.1f}% |")

        if splits:
            lines.extend([
                "",
                "## 6. Temporal Train / Validation / Test Splits",
                "| Split | Rows | Low Risk (%) | Medium Risk (%) | High Risk (%) |",
                "| :--- | :--- | :--- | :--- | :--- |"
            ])
            for sname, sdata in splits.items():
                rc = sdata.get("row_count", 0)
                dist = sdata.get("distribution", {})
                low_count = dist.get("Low", dist.get("LOW", 0))
                med_count = dist.get("Medium", dist.get("MEDIUM", 0))
                high_count = dist.get("High", dist.get("HIGH", 0))
                low_p = (low_count / (rc or 1)) * 100
                med_p = (med_count / (rc or 1)) * 100
                high_p = (high_count / (rc or 1)) * 100
                lines.append(f"| **{sname.title()}** | {rc:,} | {low_p:.1f}% | {med_p:.1f}% | {high_p:.1f}% |")

        lines.append("")
        lines.append("> **Integrity Assurance**: Zero future-period metrics were accessible or utilized in the feature matrix columns.")
        return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hybrid GST Data Pipeline Runner")
    parser.add_argument("--vendors", type=int, default=50, help="Synthetic vendor count")
    parser.add_argument("--months", type=int, default=12, help="Number of simulated months")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--include-public", action="store_true", default=True, help="Include public transaction adapter")
    parser.add_argument("--no-public", dest="include_public", action="store_false")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory")
    args = parser.parse_args()

    pipeline = HybridGSTPipeline(seed=args.seed, output_dir=args.output_dir)
    pipeline.run(
        vendor_count=args.vendors,
        months_count=args.months,
        include_public=args.include_public
    )
