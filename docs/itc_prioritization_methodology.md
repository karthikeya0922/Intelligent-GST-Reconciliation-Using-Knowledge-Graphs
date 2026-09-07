# ITC Prioritization Methodology: Risk × Exposure Matrix

## 1. Separation of Risk from Financial Exposure
A fundamental invariant of the GST ITC Risk Engine is the operational separation of **behavioral non-compliance risk** from **monetary financial exposure**:

- **Vendor A**: Claims ₹5,00,000 in ITC, files returns on time, maintains a 0.2% mismatch rate. **Risk = LOW, Exposure = HIGH**.
- **Vendor B**: Claims ₹15,000 in ITC, misses GSTR-3B filings, has a 35% mismatch rate. **Risk = HIGH, Exposure = LOW**.

Flagging Vendor A as "fraudulent" merely because the invoice amount is large causes commercial disruption. Conversely, ignoring Vendor B allows chronic non-filers to operate under the radar. The engine evaluates both dimensions simultaneously.

---

## 2. Financial Metrics & Safe Ratio Formulations

1. **Total Invoiced Tax**: Gross tax liability (CGST + SGST + IGST) invoiced in period $T_k$.
2. **ITC Exposure (INR)**: Discrepancy quantum claimed on invoices missing in supplier outward returns, exhibiting tax rate discrepancies, or lacking statutory e-Way Bills.
3. **ITC Exposure Ratio**:
   $$\text{itc\_exposure\_ratio} = \frac{\text{itc\_exposure}}{\max(\text{total\_tax}, 1.0)}$$
   *Guarantees non-negative values and prevents division by zero, NaN, or Infinity.*

---

## 3. Operational Prioritization Matrix

The system categorizes ITC Exposure as **High** if exposure exceeds ₹1,00,000 (or >20% of tax liability), and **Low** otherwise:

| Behavioral Risk Level | ITC Exposure Quantum | Assigned Review Priority | Decision-Support Recommendation |
|:---:|:---:|:---:|:---|
| **LOW** | Low ($< \text{₹}1,00,000$) | **`LOW`** | **Routine Monitoring**: No immediate audit intervention. Automated reconciliation approved. |
| **LOW** | High ($\ge \text{₹}1,00,000$) | **`MEDIUM`** | **Spot-Check Invoices**: Clean vendor profile but material ITC exposure. Verify invoice documentation. |
| **MEDIUM** | Low ($< \text{₹}1,00,000$) | **`MEDIUM`** | **Desk Review**: Reconcile minor tax mismatches or late return filing delays before return finalization. |
| **MEDIUM** | High ($\ge \text{₹}1,00,000$) | **`HIGH`** | **Provisional ITC Hold**: Moderate discrepancy signals with material exposure. Request supplier confirmation. |
| **HIGH** | Low ($< \text{₹}1,00,000$) | **`HIGH`** | **Investigate Non-Compliance**: Severe behavioral risk flagged despite modest exposure. Review counterparty network. |
| **HIGH** | High ($\ge \text{₹}1,00,000$) | **`CRITICAL`** | **Priority Audit & Rule 36(4) Blockage**: Severe risk coupled with major financial exposure. Initiate statutory inspection. |
