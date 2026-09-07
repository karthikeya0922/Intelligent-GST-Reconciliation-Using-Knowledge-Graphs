# Ground-Truth Labeling Methodology & Leakage Prevention

> [!NOTE]
> **Data Provenance Notice**  
> The system uses a hybrid dataset consisting of publicly available transaction data and controlled synthetic GST-specific records. Public data provides realistic transaction distributions, while synthetic data introduces GST-specific filing, reconciliation, ITC, and compliance scenarios that are not available in most public datasets.

---

## 1. The Core ML Objective

The machine learning goal is to predict **future vendor non-compliance and ITC risk** based on historical filing behavior, invoice consistency, and network topology.

```text
Historical Observation Window [t - k ... t]          Future Evaluation Period [t + 1]
┌──────────────────────────────────────────┐          ┌──────────────────────────────┐
│ Features:                                │          │ Ground-Truth Target Outcome: │
│ - Past filing delays                     │          │ - Did vendor default on 3B?  │
│ - Historical mismatch rate               │ ───────> │ - Were returns missing?      │
│ - Transaction volumes & ticket sizes     │          │ - Did new mismatches emerge? │
│ - Graph degree & circular connections    │          │                              │
└──────────────────────────────────────────┘          └──────────────┬───────────────┘
                                                                     │
                                                              Score & Categorize:
                                                        [Low | Medium | High Risk]
```

---

## 2. Prevention of Temporal Data Leakage

A critical flaw in naive ML pipelines is data leakage: computing features on data that includes the prediction period or future outcomes.

### Strict Boundary Rules:
1. **Feature Vector Isolation**:
   Every feature row associated with observation period $T_k$ is computed **strictly and solely** from transactions, filings, and reconciliations occurring in or prior to period $T_k$.
2. **Target Computation Isolation**:
   The target outcome (`target_risk_score`, `target_risk_label`) is evaluated **strictly and solely** on period $T_{k+1}$.
3. **Zero Future Contamination**:
   Under no circumstances is any invoice, filing date, or discrepancy from period $T_{k+1}$ allowed to enter any feature column for period $T_k$.

Automated tests in `tests/data/test_features.py::test_zero_future_data_leakage` verify this boundary invariant on every pipeline run.

---

## 3. Ground-Truth Scoring Formula

Target risk is not assigned at random. It is deterministically calculated from observable statutory non-compliance events in the target evaluation period using the following configurable penalty weights:

$$\text{RiskScore} = \min\left(1.0, \sum w_i \cdot P_i\right)$$

Where:
- $w_{\text{GSTR-3B}} = 0.35$ : Tax collected from buyer but not remitted to Government.
- $w_{\text{GSTR-1}} = 0.20$ : Failure to file outward return, blocking buyer's ITC under Section 16(2)(aa).
- $w_{\text{mismatch}} = 0.20$ : Proportion of mismatched invoices in target period.
- $w_{\text{delay}} = 0.10$ : Normalized filing delay ($\min(\text{delay}/30, 1.0)$).
- $w_{\text{duplicate}} = 0.10$ : Submission of duplicate/near-duplicate invoices.
- $w_{\text{einvoice}} = 0.05$ : Regulatory non-compliance on e-invoice IRNs.

### Target Risk Classification

| Target Risk Score | Target Risk Label | Action / Implication |
| :--- | :--- | :--- |
| **Score $< 0.30$** | **Low Risk** | Full compliance; safe for automated ITC credit claiming. |
| **$0.30 \le \text{Score} < 0.60$** | **Medium Risk** | Filing irregularities; flagged for auditor review. |
| **Score $\ge 0.60$** | **High Risk** | Severe non-compliance or tax default; ITC provisional block. |
