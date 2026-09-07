# Risk Scoring Methodology: ML Risk Indicator Score

## 1. Overview & Separation of Concepts
The production GST ITC risk engine explicitly differentiates between three core constructs:
1. **Financial ITC Exposure (INR)**: The monetary amount of Input Tax Credit associated with disputed, unmatched, or non-compliant invoices.
2. **Machine Learning Risk Probability**: The calibrated multi-class probability distribution produced by the frozen Tabular XGBoost model:
   $$\{P(\text{LOW}), P(\text{MEDIUM}), P(\text{HIGH})\}, \quad \sum_{c} P(c) = 1.0$$
3. **ML Risk Indicator Score (0–100)**: A normalized continuous operational risk index summarizing expected non-compliance severity.

> [!IMPORTANT]
> The **ML Risk Indicator Score** is an automated decision-support metric designed for audit workflow prioritization. It does **not** constitute an official statutory GST risk score, judicial adjudication of fraud, or legal tax determination.

---

## 2. Mathematical Definition
The normalized score scales from $0.0$ to $100.0$ according to the expected severity weight:

$$\text{risk\_score} = 100 \times \left( P(\text{MEDIUM}) \times 0.5 + P(\text{HIGH}) \times 1.0 \right)$$

### Canonical Verification Cases:
- **Case 1**: $P(\text{Medium}) = 0.0, P(\text{High}) = 0.0 \implies \text{Score} = 0.0$
- **Case 2**: $P(\text{Medium}) = 1.0, P(\text{High}) = 0.0 \implies \text{Score} = 50.0$
- **Case 3**: $P(\text{Medium}) = 0.0, P(\text{High}) = 1.0 \implies \text{Score} = 100.0$
- **Case 4**: $P(\text{Low}) = 0.2, P(\text{Medium}) = 0.3, P(\text{High}) = 0.5 \implies \text{Score} = 100 \times (0.3 \times 0.5 + 0.5 \times 1.0) = 65.0$

---

## 3. Application-Level Presentation Risk Bands
For UI presentation and operational filtering, the score is mapped into three standardized tiers:

| Score Interval | Presentation Band | Operational Intent |
|:---:|:---:|:---|
| **$0.0 \le \text{Score} \le 33.0$** | **`LOW`** | Clean compliance history. Automated reconciliation approved for ITC claiming. |
| **$33.0 < \text{Score} \le 66.0$** | **`MEDIUM`** | Moderate non-compliance or filing delays. Targeted desk review recommended. |
| **$66.0 < \text{Score} \le 100.0$** | **`HIGH`** | High probability of non-filing or severe invoice discrepancy. Priority audit inspection. |

### Model Class vs. Risk Band Independence
The engine separately reports the model's argmax class (`model_class`) and the application score band (`risk_band`). For example, in borderline probability distributions ($P(\text{Low})=0.05, P(\text{Medium})=0.48, P(\text{High})=0.47$), the model's predicted class is `MEDIUM` while the continuous score is $71.0$ (`HIGH` band). Preserving both prevents silent label overwriting.
