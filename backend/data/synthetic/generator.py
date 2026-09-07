"""
Master Synthetic GST Dataset Generator.

Generates temporal multi-month GST ecosystems:
Vendors -> Invoices -> Filings -> Reconciliations -> Graph Syndicate Topology.
Supports deterministic seeds and configurable vendor and month counts.
"""

import argparse
from datetime import date, timedelta
from decimal import Decimal
import json
import os
import random
from typing import List, Dict, Tuple, Any

from backend.data.schema import (
    Vendor, Invoice, Filing, Reconciliation, DataSource
)
from backend.data.synthetic.profiles import PROFILES, VendorBehaviorProfile
from backend.data.synthetic.vendors import VendorGenerator
from backend.data.synthetic.invoices import InvoiceGenerator
from backend.data.synthetic.compliance import ComplianceGenerator
from backend.data.synthetic.anomalies import AnomalyEngine, AnomalyType, AnomalySeverity


class SyntheticGSTDatasetGenerator:
    """Orchestrates deterministic multi-period generation of GST ecosystems."""

    def __init__(self, seed: int = 42, buyer_state: str = "Karnataka", buyer_gstin: str = "29AAQCQ1234M1Z8"):
        self.seed = seed
        self.rng = random.Random(seed)
        self.vendor_gen = VendorGenerator(seed=seed)
        self.invoice_gen = InvoiceGenerator(buyer_state=buyer_state, buyer_gstin=buyer_gstin, seed=seed)
        self.compliance_gen = ComplianceGenerator(seed=seed)
        self.anomaly_engine = AnomalyEngine(seed=seed)

    def generate_tax_periods(self, start_year: int = 2024, start_month: int = 4, months_count: int = 12) -> List[str]:
        """Generate a list of YYYY-MM tax periods."""
        periods = []
        cur_y = start_year
        cur_m = start_month
        for _ in range(months_count):
            periods.append(f"{cur_y:04d}-{cur_m:02d}")
            cur_m += 1
            if cur_m > 12:
                cur_m = 1
                cur_y += 1
        return periods

    def generate_dataset(
        self,
        vendor_count: int = 100,
        months_count: int = 12,
        invoices_per_vendor_month: int = 3
    ) -> Dict[str, Any]:
        """
        Executes full generation run.
        Returns dictionary containing:
        - vendors
        - invoices
        - filings
        - reconciliations
        - anomaly_log
        - network_edges (graph topology)
        """
        vendors = self.vendor_gen.generate_vendors(count=vendor_count)
        periods = self.generate_tax_periods(start_year=2024, start_month=4, months_count=months_count)

        all_invoices: List[Invoice] = []
        all_filings: List[Filing] = []
        all_reconciliations: List[Reconciliation] = []
        inv_counter = 1

        # Track dynamic profile state per vendor across time (behavioral persistence)
        vendor_profiles = {v.vendor_id: getattr(v, "synthetic_profile", "A") for v in vendors}

        # Rich graph scenario construction
        graph_edges: List[Dict[str, Any]] = []
        vendor_list = list(vendors)
        v_count = len(vendor_list)

        if v_count >= 6:
            # 1. Normal Tiered Supply Chain (A -> B -> C)
            graph_edges.append({
                "source_vendor": vendor_list[0].vendor_id,
                "target_vendor": vendor_list[1].vendor_id,
                "relation": "SUPPLY_CHAIN",
                "topology": "normal_tier"
            })
            graph_edges.append({
                "source_vendor": vendor_list[1].vendor_id,
                "target_vendor": vendor_list[2].vendor_id,
                "relation": "SUPPLY_CHAIN",
                "topology": "normal_tier"
            })

            # 2. Dense Legitimate Industrial Cluster (A -> B, A -> C, B -> C, C -> D)
            graph_edges.append({
                "source_vendor": vendor_list[2].vendor_id,
                "target_vendor": vendor_list[3].vendor_id,
                "relation": "SUPPLY_CLUSTER",
                "topology": "dense_legitimate"
            })
            graph_edges.append({
                "source_vendor": vendor_list[3].vendor_id,
                "target_vendor": vendor_list[4].vendor_id,
                "relation": "SUPPLY_CLUSTER",
                "topology": "dense_legitimate"
            })

            # 3. Bilateral Trading Relationship (A <-> B)
            graph_edges.append({
                "source_vendor": vendor_list[4].vendor_id,
                "target_vendor": vendor_list[5].vendor_id,
                "relation": "BILATERAL_TRADE",
                "topology": "bilateral"
            })
            graph_edges.append({
                "source_vendor": vendor_list[5].vendor_id,
                "target_vendor": vendor_list[4].vendor_id,
                "relation": "BILATERAL_TRADE",
                "topology": "bilateral"
            })

            # 4. Legitimate Industrial Recycling Loop (non-fraud cycle: scrap supplier -> mill -> fabricator -> scrap)
            if v_count >= 9:
                for i in range(6, 9):
                    src = vendor_list[i]
                    dst = vendor_list[6 if i == 8 else i + 1]
                    graph_edges.append({
                        "source_vendor": src.vendor_id,
                        "target_vendor": dst.vendor_id,
                        "relation": "RECYCLING_SUPPLY_LOOP",
                        "topology": "legitimate_cycle"
                    })

        # 5. Suspicious Circular Ring (Profile G syndicate clique)
        profile_g_vendors = [v for v in vendors if getattr(v, "synthetic_profile", "A") == "G"]
        if len(profile_g_vendors) >= 3:
            for i in range(len(profile_g_vendors)):
                src = profile_g_vendors[i]
                dst = profile_g_vendors[(i + 1) % len(profile_g_vendors)]
                graph_edges.append({
                    "source_vendor": src.vendor_id,
                    "target_vendor": dst.vendor_id,
                    "relation": "CIRCULAR_SYNDICATE_LOOP",
                    "topology": "suspicious_cycle"
                })

        from backend.data.synthetic.profiles import sample_profile_transition

        for period_idx, period in enumerate(periods):
            year, month = map(int, period.split("-"))
            is_quarter_boundary = (period_idx > 0 and period_idx % 3 == 0)

            for vendor in vendors:
                vid = vendor.vendor_id
                
                # Quarterly controlled profile drift
                if is_quarter_boundary:
                    vendor_profiles[vid] = sample_profile_transition(vendor_profiles[vid], self.rng)
                
                current_prof_code = vendor_profiles[vid]
                profile = PROFILES.get(current_prof_code, PROFILES["A"])

                # 1. Generate monthly Filing record
                filing = self.compliance_gen.generate_filings_for_period(
                    vendor_id=vid,
                    tax_period=period,
                    profile=profile
                )
                all_filings.append(filing)

                # Log filing anomalies
                if not filing.gstr1_filed:
                    self.anomaly_engine.log_custom_anomaly(
                        anomaly_type=AnomalyType.MISSING_GSTR1,
                        severity=AnomalySeverity.HIGH,
                        invoice_id=f"FILING-{vid}-{period}",
                        vendor_id=vid,
                        tax_period=period,
                        affected_fields=["gstr1_filed"],
                        explanation="Supplier omitted GSTR-1 sales return filing"
                    )
                if not filing.gstr3b_filed:
                    self.anomaly_engine.log_custom_anomaly(
                        anomaly_type=AnomalyType.MISSING_GSTR3B,
                        severity=AnomalySeverity.CRITICAL,
                        invoice_id=f"FILING-{vid}-{period}",
                        vendor_id=vid,
                        tax_period=period,
                        affected_fields=["gstr3b_filed"],
                        explanation="Supplier defaulted on GSTR-3B tax remittance"
                    )
                if filing.filing_delay_days > 15:
                    self.anomaly_engine.log_custom_anomaly(
                        anomaly_type=AnomalyType.LATE_FILING,
                        severity=AnomalySeverity.MEDIUM,
                        invoice_id=f"FILING-{vid}-{period}",
                        vendor_id=vid,
                        tax_period=period,
                        affected_fields=["filing_delay_days"],
                        explanation=f"Supplier delayed statutory filing by {filing.filing_delay_days} days"
                    )

                # 2. Generate monthly invoices
                count_for_month = max(1, self.rng.randint(invoices_per_vendor_month - 1, invoices_per_vendor_month + 2))
                if current_prof_code == "F":
                    count_for_month = max(1, count_for_month // 2)

                for _ in range(count_for_month):
                    day = self.rng.randint(1, 28)
                    inv_date = date(year, month, day)

                    base_invoice = self.invoice_gen.generate_invoice_for_vendor(
                        vendor=vendor,
                        inv_index=inv_counter,
                        invoice_date=inv_date,
                        profile=profile
                    )
                    inv_counter += 1

                    # 3. Anomaly Injection across spectrum
                    invoice = base_invoice
                    rand_val = self.rng.random()
                    if rand_val < profile.tax_error_probability:
                        invoice = self.anomaly_engine.inject_tax_mismatch(invoice)
                    elif rand_val < (profile.tax_error_probability + 0.05):
                        invoice = self.anomaly_engine.inject_taxable_value_mismatch(invoice)
                    elif rand_val < (profile.mismatch_probability * 0.2):
                        invoice = self.anomaly_engine.inject_hsn_mismatch(invoice)
                    elif rand_val < (profile.mismatch_probability * 0.25):
                        invoice = self.anomaly_engine.inject_date_mismatch(invoice)
                    elif current_prof_code == "G" and rand_val < 0.08:
                        invoice = self.anomaly_engine.inject_unusual_transaction(invoice)

                    all_invoices.append(invoice)

                    # 4. Generate Reconciliation record
                    recon = self.compliance_gen.generate_reconciliation_record(
                        invoice=invoice,
                        filing=filing,
                        profile=profile
                    )
                    all_reconciliations.append(recon)

                    # Log e-Invoice / e-Way Bill anomalies if missing
                    if not recon.einvoice_present:
                        self.anomaly_engine.log_custom_anomaly(
                            anomaly_type=AnomalyType.MISSING_EINVOICE,
                            severity=AnomalySeverity.LOW,
                            invoice_id=invoice.invoice_id,
                            vendor_id=vid,
                            tax_period=period,
                            affected_fields=["einvoice_present"],
                            explanation="Invoice lacks mandatory e-invoice IRN"
                        )
                    if not recon.ewaybill_present:
                        self.anomaly_engine.log_custom_anomaly(
                            anomaly_type=AnomalyType.MISSING_EWAY_BILL,
                            severity=AnomalySeverity.LOW,
                            invoice_id=invoice.invoice_id,
                            vendor_id=vid,
                            tax_period=period,
                            affected_fields=["ewaybill_present"],
                            explanation="Consignment over ₹50,000 lacks e-Way Bill coverage"
                        )

                    # 5. Profile H duplicate / near-duplicate generation
                    if current_prof_code == "H" and self.rng.random() < profile.duplicate_probability:
                        near_dup = self.rng.random() > 0.5
                        dup_inv = self.anomaly_engine.create_duplicate_invoice(invoice, near_duplicate=near_dup)
                        all_invoices.append(dup_inv)
                        
                        dup_recon = self.compliance_gen.generate_reconciliation_record(
                            invoice=dup_inv,
                            filing=filing,
                            profile=profile
                        )
                        dup_recon.reconciliation_status = "Duplicate Invoice"
                        all_reconciliations.append(dup_recon)

        return {
            "vendors": vendors,
            "invoices": all_invoices,
            "filings": all_filings,
            "reconciliations": all_reconciliations,
            "anomalies": self.anomaly_engine.anomaly_log,
            "graph_edges": graph_edges,
            "syndicate_edges": graph_edges,
            "tax_periods": periods,
            "metadata": {
                "seed": self.seed,
                "vendor_count": len(vendors),
                "invoice_count": len(all_invoices),
                "filing_count": len(all_filings),
                "months_count": len(periods),
            }
        }


SyntheticGSTGenerator = SyntheticGSTDatasetGenerator



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Synthetic GST Dataset Generator")
    parser.add_argument("--vendors", type=int, default=50, help="Number of vendors to simulate")
    parser.add_argument("--months", type=int, default=12, help="Number of tax months to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--output", type=str, default="data/sample/synthetic_gst_sample.json")
    args = parser.parse_args()

    gen = SyntheticGSTDatasetGenerator(seed=args.seed)
    dataset = gen.generate_dataset(vendor_count=args.vendors, months_count=args.months)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        # Dump summary
        json.dump({
            "metadata": dataset["metadata"],
            "vendor_sample_count": len(dataset["vendors"]),
            "invoice_sample_count": len(dataset["invoices"]),
            "anomalies_injected": len(dataset["anomalies"])
        }, f, indent=2)
    
    print(f"Generated {len(dataset['vendors'])} vendors, {len(dataset['invoices'])} invoices across {args.months} months.")
    print(f"Saved summary to {args.output}")
