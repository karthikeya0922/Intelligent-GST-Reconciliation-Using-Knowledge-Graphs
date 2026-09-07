# Investigation Workflow & Auditor Workstation

## 1. Overview

The **Investigation Workspace** (`/investigation` and `/investigation/:vendor_id`) serves as the primary operational demonstration interface. It synthesizes statistical machine learning outputs, monetary discrepancy quantifications, granular reconciliation evidence, and network context into a structured, audit-ready sequence.

---

## 2. 8-Step Auditor Review Flow

```
[ Step 1: Vendor Identity ]
          ↓
[ Step 2: Review ML Risk Score ]
          ↓
[ Step 3: Review Financial ITC Exposure ]
          ↓
[ Step 4: Review Tree SHAP Explanations ]
          ↓
[ Step 5: Review Reconciliation Discrepancies ]
          ↓
[ Step 6: Review Statutory Compliance Filings ]
          ↓
[ Step 7: Inspect Knowledge Graph Topology ]
          ↓
[ Step 8: Confirm Operational Priority & Action ]
```

### Detailed Step Breakdown

1. **Step 1 — Entity Demographics & Baseline Registration:**
   * Taxpayer ID, legal name, GSTIN, jurisdiction, business category.
   * Turnover volume and billed tax baseline.

2. **Step 2 — Predictive ML Risk Indicator:**
   * Review the 0–100 continuous score and presentation risk band (`LOW`, `MEDIUM`, `HIGH`).
   * Inspect individual class probabilities ($P(\text{LOW})$, $P(\text{MED})$, $P(\text{HIGH})$).

3. **Step 3 — Financial ITC Exposure Quantification:**
   * Independent evaluation of monetary exposure magnitude.
   * Exposure ratio against cumulative tax billed.

4. **Step 4 — Tree SHAP Factor Attribution:**
   * Exact additive Shapley contributions for feature importance.
   * Review upward risk drivers alongside mitigating protective factors.

5. **Step 5 — Invoice Reconciliation Audit:**
   * Discrepancy counts across GSTR-2B vs. internal books.
   * Taxable value mismatches, duplicate invoices, and missing e-Invoice IRN / e-Way bill coverages.

6. **Step 6 — Statutory Return Filings:**
   * Historical filing delay days across returns.
   * Identification of missing GSTR-1 sales returns or defaulted GSTR-3B tax remittances.

7. **Step 7 — Knowledge Graph Topology Inspection:**
   * Verification of supplier and customer concentration percentages.
   * Evaluation of reciprocal bilateral trading ties and circular trade paths.

8. **Step 8 — Operational Review Decision:**
   * Selection of operational intervention: routine monitoring, targeted desk audit, provisional ITC credit hold, or pre-claim audit block.
   * One-click **Export Audit File** generating a timestamped JSON dossier for statutory recordkeeping.
