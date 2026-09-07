# Model Explainability & Narrative Decision Support

## 1. Class-Specific Tree SHAP Attributions
In statutory tax administration, black-box predictions lack regulatory defensibility. The GST ITC Risk Engine incorporates native C++ Tree SHAP to quantify the exact contribution of each feature toward the predicted class:

$$\text{Margin}(x, c) = \phi_{0, c} + \sum_{j=1}^{19} \phi_{j, c}(x)$$

Where:
- $c \in \{\text{LOW}, \text{MEDIUM}, \text{HIGH}\}$ is the predicted class.
- $\phi_{j, c}$ is the Shapley attribution of feature $j$.
- A positive $\phi_{j, c} > 0$ indicates the feature pushed the decision toward class $c$.

> [!NOTE]
> **Non-Causal Language Requirement**: SHAP attributions quantify model reliance, not real-world causation. Reports must state *"This feature contributed to the model's HIGH-risk prediction"* rather than *"This feature caused the vendor to be high risk"*.

---

## 2. Narrative Explanation Format
The engine synthesizes quantitative metrics into an auditor-facing narrative:

```text
Vendor V1023 is classified as HIGH risk (Model Prediction) with an ML Risk Indicator Score of 82.4/100 (HIGH Priority Band) for period 2026-03.

Key Model Risk Drivers (Tree SHAP):
- statutory return filing delay (high impact, SHAP: +0.452)
- invoice reconciliation discrepancy severity (high impact, SHAP: +0.321)
- repeated late return submissions (medium impact, SHAP: +0.184)
- historical compliance risk rating (medium impact, SHAP: +0.115)

Financial ITC Exposure:
₹1,25,000.00 (31.0% of invoiced tax liability currently at risk of clawback).

Operational Review Priority: CRITICAL.
Recommended Action: Priority audit and Rule 36(4) ITC blockage review. Initiate statutory inspection.

Disclaimer: This assessment is an automated machine-learning risk indicator designed solely for audit prioritization and decision support. It does not constitute an official statutory GST tax assessment, judicial determination of fraud, or legal finding of tax liability.
```
