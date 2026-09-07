# Data Quality Standards & Validation Rules

> [!NOTE]
> **Data Provenance Notice**  
> The system uses a hybrid dataset consisting of publicly available transaction data and controlled synthetic GST-specific records. Public data provides realistic transaction distributions, while synthetic data introduces GST-specific filing, reconciliation, ITC, and compliance scenarios that are not available in most public datasets.

---

## 1. Quality Invariants

The data foundation validates all datasets (both external public datasets and synthetic populations) against 5 statutory invariants:

### 1. Invoice Arithmetic Invariant
$$\text{TotalTax} = \text{CGST} + \text{SGST} + \text{IGST} \pm ₹0.02$$
$$\text{InvoiceValue} = \text{TaxableValue} + \text{TotalTax} \pm ₹0.05$$
Negative values are strictly prohibited on all financial fields.

### 2. Statutory Jurisdiction Invariant
- **Intra-state Supply**:
  $$\text{IGST} = ₹0.00, \quad |\text{CGST} - \text{SGST}| \le ₹0.02$$
- **Inter-state Supply**:
  $$\text{CGST} = ₹0.00, \quad \text{SGST} = ₹0.00, \quad \text{IGST} = \text{TotalTax}$$

### 3. GSTIN Format Invariant
Must match the statutory regex:
`^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`
with state code matching one of the 37 official Indian state and UT codes.

### 4. Temporal Chronology Invariant
Filing dates cannot precede the transaction date. Filing delays are calculated against statutory deadlines:
- GSTR-1: 11th of the subsequent month.
- GSTR-3B: 20th of the subsequent month.

### 5. Duplicate Invariant
Distinguishes intentional test duplicates (flagged with `is_duplicate=True` or anomaly tags) from accidental pipeline duplicates. Any accidental duplicate causes pipeline validation to fail.

---

## 2. Automated Quality Reporting

Every pipeline run produces two artifacts:

1. **Machine-Readable JSON**:
   `data/reports/data_quality_report.json`
   Contains raw counts, validation booleans, profile distributions, and execution durations.

2. **Human-Readable Markdown**:
   `data/reports/data_quality_report.md`
   Summary tables of validation status, anomaly breakdowns, behavioral profiles, and target distributions.
