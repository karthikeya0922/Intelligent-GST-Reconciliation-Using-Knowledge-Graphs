"""
Feature & Dataset Distribution Analysis Module.

Calculates descriptive statistics (mean, median, std, min, max, p25, p75, missing)
across all numerical feature vectors, detects unrealistic distributions,
and compares public vs synthetic feature alignments.
"""

from typing import List, Dict, Any, Tuple
import json
import os
import numpy as np
import pandas as pd

from backend.data.schema import Invoice, DataSource


NUMERICAL_FEATURES = [
    "invoice_count",
    "total_invoice_value",
    "average_invoice_value",
    "total_tax",
    "mismatch_count",
    "mismatch_rate",
    "missing_gstr1_count",
    "missing_gstr3b_count",
    "late_filing_count",
    "average_filing_delay",
    "duplicate_invoice_count",
    "missing_einvoice_count",
    "missing_eway_bill_count",
    "itc_exposure",
    "supplier_relationship_count",
    "graph_degree",
    "previous_period_risk",
]


class DistributionAnalyzer:
    """Analyzes feature matrix distributions, detects anomalies, and outputs reports."""

    def analyze_features(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics for all numerical features."""
        stats = {}
        for col in NUMERICAL_FEATURES:
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                if len(series) > 0:
                    med = round(float(series.median()), 4)
                    stats[col] = {
                        "count": int(len(series)),
                        "mean": round(float(series.mean()), 4),
                        "median": med,
                        "p50": med,
                        "std": round(float(series.std()), 4) if len(series) > 1 else 0.0,
                        "min": round(float(series.min()), 4),
                        "max": round(float(series.max()), 4),
                        "p25": round(float(series.quantile(0.25)), 4),
                        "p75": round(float(series.quantile(0.75)), 4),
                        "skewness": round(float(series.skew()), 4) if len(series) > 2 else 0.0,
                        "missing_count": int(df[col].isna().sum())
                    }
                else:
                    stats[col] = {"count": 0, "missing_count": len(df)}
        return stats

    def compute_feature_statistics(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Alias for analyze_features."""
        return self.analyze_features(df)

    def detect_distribution_warnings(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Identify potential generation problems: near-zero variance, high correlation, negatives."""
        warnings = []
        
        # 1. Negative values check
        for col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            neg_count = (s < 0).sum()
            if neg_count > 0:
                warnings.append({
                    "type": "NEGATIVE_VALUES",
                    "level": "ERROR",
                    "feature": col,
                    "message": f"Detected {neg_count} impossible negative values in feature '{col}'."
                })

        # 2. Near-zero variance check
        for col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) > 1 and s.std() < 1e-5:
                warnings.append({
                    "type": "NEAR_ZERO_VARIANCE",
                    "level": "WARNING",
                    "feature": col,
                    "message": f"Feature '{col}' has near-zero variance (std={s.std():.6f})."
                })

        # 3. Pairwise high correlation check (> 0.98)
        avail_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if len(avail_cols) > 1:
            corr_matrix = df[avail_cols].corr().abs()
            for i in range(len(avail_cols)):
                for j in range(i + 1, len(avail_cols)):
                    c1, c2 = avail_cols[i], avail_cols[j]
                    val = corr_matrix.loc[c1, c2]
                    # Exclude trivial arithmetic identity (total_tax vs total_invoice_value which can naturally correlate)
                    if val > 0.98 and not (c1.startswith("total_") and c2.startswith("total_")):
                        warnings.append({
                            "type": "EXTREME_CORRELATION",
                            "level": "WARNING",
                            "feature": f"{c1} <-> {c2}",
                            "message": f"Features '{c1}' and '{c2}' have suspiciously high correlation (r={val:.4f})."
                        })

        return warnings

    def detect_distribution_anomalies(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """Alias for detect_distribution_warnings."""
        return self.detect_distribution_warnings(df)

    def compare_public_vs_synthetic(self, invoices: List[Invoice]) -> Dict[str, Any]:
        """Compare distribution of transaction amounts between public and synthetic records."""
        pub_vals = [float(i.taxable_value) for i in invoices if i.data_source == DataSource.PUBLIC]
        syn_vals = [float(i.taxable_value) for i in invoices if i.data_source == DataSource.SYNTHETIC]

        pub_stats = {
            "count": len(pub_vals),
            "mean": round(float(np.mean(pub_vals)), 2) if pub_vals else 0.0,
            "median": round(float(np.median(pub_vals)), 2) if pub_vals else 0.0,
            "std": round(float(np.std(pub_vals)), 2) if pub_vals else 0.0,
        }
        syn_stats = {
            "count": len(syn_vals),
            "mean": round(float(np.mean(syn_vals)), 2) if syn_vals else 0.0,
            "median": round(float(np.median(syn_vals)), 2) if syn_vals else 0.0,
            "std": round(float(np.std(syn_vals)), 2) if syn_vals else 0.0,
        }

        # Check if mean orders of magnitude diverge by more than 50x
        divergence_warning = None
        if pub_stats["mean"] > 0 and syn_stats["mean"] > 0:
            ratio = max(pub_stats["mean"] / syn_stats["mean"], syn_stats["mean"] / pub_stats["mean"])
            if ratio > 50.0:
                divergence_warning = f"Significant scale difference: mean transaction values differ by {ratio:.1f}x."

        return {
            "public_invoices": pub_stats,
            "synthetic_invoices": syn_stats,
            "compatibility_status": "COMPATIBLE" if not divergence_warning else "WARNING",
            "warning": divergence_warning
        }

    def generate_report(
        self,
        df: pd.DataFrame,
        invoices: List[Invoice],
        output_dir: str = "data/reports"
    ) -> Dict[str, Any]:
        """Generates both JSON and Markdown reports."""
        os.makedirs(output_dir, exist_ok=True)

        stats = self.analyze_features(df)
        warnings = self.detect_distribution_warnings(df)
        compatibility = self.compare_public_vs_synthetic(invoices)

        report_payload = {
            "feature_statistics": stats,
            "distribution_warnings": warnings,
            "distribution_anomalies": warnings,
            "public_synthetic_compatibility": compatibility
        }

        json_path = os.path.join(output_dir, "feature_distribution_report.json")
        md_path = os.path.join(output_dir, "feature_distribution_report.md")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=2)

        md_content = self._format_markdown(stats, warnings, compatibility)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return report_payload

    def _format_markdown(
        self,
        stats: Dict[str, Dict[str, float]],
        warnings: List[Dict[str, str]],
        compatibility: Dict[str, Any]
    ) -> str:
        lines = [
            "# Feature Distribution & Statistical Validation Report",
            "",
            "## 1. Numerical Feature Statistics",
            "",
            "| Feature | Count | Mean | Median | Std | Min | Max | P25 | P75 | Missing |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ]
        for col, s in stats.items():
            lines.append(
                f"| `{col}` | {s['count']} | {s['mean']:,} | {s['median']:,} | {s['std']:,} | "
                f"{s['min']:,} | {s['max']:,} | {s['p25']:,} | {s['p75']:,} | {s['missing_count']} |"
            )

        lines.extend([
            "",
            "## 2. Statistical Distribution Health Checks",
            ""
        ])
        if not warnings:
            lines.append("No statistical anomalies, near-zero variance features, or negative values detected.")
        else:
            for w in warnings:
                lines.append(f"- **[{w['level']}]** {w['feature']}: {w['message']}")

        lines.extend([
            "",
            "## 3. Public vs Synthetic Distribution Compatibility",
            "",
            f"- **Public Transactions Analyzed**: {compatibility['public_invoices']['count']:,} "
            f"(Mean: ₹{compatibility['public_invoices']['mean']:,}, Median: ₹{compatibility['public_invoices']['median']:,})",
            f"- **Synthetic Transactions Analyzed**: {compatibility['synthetic_invoices']['count']:,} "
            f"(Mean: ₹{compatibility['synthetic_invoices']['mean']:,}, Median: ₹{compatibility['synthetic_invoices']['median']:,})",
            f"- **Compatibility Status**: `{compatibility['compatibility_status']}`",
        ])
        if compatibility["warning"]:
            lines.append(f"> **Warning**: {compatibility['warning']}")
        else:
            lines.append("> **Note**: Public and synthetic transactions exhibit mutually plausible enterprise order values.")

        return "\n".join(lines)
