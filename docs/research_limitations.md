# Research Limitations & Ethical Governance

## 1. Research Scope & Dataset Boundaries

* **Controlled Hybrid Benchmark:** The 2,015 vendors, 168,213 invoices, and 24 simulated months comprise a controlled research benchmark designed to replicate structural GST patterns (mismatches, timing delays, syndicate rings, industrial clusters) without exposing proprietary commercial records.
* **External Validation Prerequisite:** While internal temporal cross-validation demonstrates high predictive fidelity (macro-F1 $\approx 0.88$ on holdout test periods), external validation against enterprise-grade or tax authority datasets is essential before live statutory or regulatory deployment.
* **Concept Drift & Real-World Calibration:** Real-world tax legislation (such as GST council rule amendments, threshold modifications, and sector-specific exemptions) may introduce shifts in invoice distributions that require ongoing periodic model recalibration.

---

## 2. Research Integrity & Language Governance

The system is engineered as an **objective decision-support and audit triage tool**. All documentation, UI interfaces, and API responses strictly adhere to neutral, non-accusatory terminology:

| ❌ Prohibited Terminology | ✅ Mandatory Governed Terminology |
| :--- | :--- |
| "Confirmed fraud" / "Fraudulent vendor" | "ML-based risk indicator" / "High risk band entity" |
| "Proves tax evasion" / "Guilty taxpayer" | "Contributed to model prediction" / "Discrepancy signal" |
| "Fraud syndicate network" | "Structural trading cluster" / "Network topology signal" |
| "Statutory tax determination" | "Decision-support triage recommendation" |
| "Statutory non-compliance confirmed" | "Reconciliation mismatch observation" |

---

## 3. Preservation of Negative Findings (Phase 2.1)

In scientific research, negative and neutral findings are as vital as positive results. Phase 4 explicitly documents and displays the Phase 2.1 ablation result:
> **Empirical Finding:** Knowledge Graph-derived topological features did not provide statistically significant predictive improvement over the 19-feature tabular XGBoost baseline on the controlled benchmark.
>
> **Design Decision:** The system preserves the Knowledge Graph exclusively as an investigation, evidence-aggregation, and network exploration layer, avoiding artificial predictive claims or synthetic GNN feature inflations.
