# Canonical GST Transaction & Compliance Schema Reference

> [!NOTE]
> **Data Provenance Notice**  
> The system uses a hybrid dataset consisting of publicly available transaction data and controlled synthetic GST-specific records. Public data provides realistic transaction distributions, while synthetic data introduces GST-specific filing, reconciliation, ITC, and compliance scenarios that are not available in most public datasets.

---

## 1. Schema Principles & Precision

All monetary fields throughout the GST ReconcileAI data foundation use **Python `Decimal` arithmetic** quantized to 2 decimal places (paise precision, `Decimal('0.01')`). Floating-point approximations (`float`) are strictly barred from financial arithmetic to avoid floating-point drift and compliance discrepancies.

---

## 2. Entity Models

### 2.1. Vendor (`backend/data/schema.py`)
Represents an active or historical commercial vendor registered under GST.

| Field | Type | Description |
| :--- | :--- | :--- |
| `vendor_id` | `str` | System-unique vendor code, e.g. `V0001` or `V-PUB-001` |
| `vendor_name` | `str` | Commercial legal or trade name |
| `gstin` | `str` | 15-character statutory GSTIN (validated format) |
| `state` | `str` | State jurisdiction name (e.g. Karnataka, Maharashtra) |
| `state_code` | `str` | 2-digit statutory state code (e.g. `29`, `27`) |
| `business_category` | `str` | Business sector (e.g. Industrial Machinery, Pharma) |
| `registration_date` | `date` | Date of GST registration |
| `is_active` | `bool` | Current GST registration status |
| `synthetic_profile` | `Optional[str]` | Assigned behavioral profile (`A` through `H`) |

---

### 2.2. Invoice (`backend/data/schema.py`)
Represents an individual B2B tax invoice issued by a vendor.

| Field | Type | Description |
| :--- | :--- | :--- |
| `invoice_id` | `str` | Unique system invoice identifier, e.g. `V0001-INV-2024-0001` |
| `vendor_id` | `str` | Issuing supplier ID |
| `buyer_id` | `str` | Recipient / Taxpayer claiming ITC (`TP001`) |
| `vendor_gstin` | `str` | Supplier GSTIN |
| `buyer_gstin` | `str` | Buyer GSTIN (`29AAQCQ1234M1Z8`) |
| `invoice_number` | `str` | Supplier's internal invoice number, e.g. `INV-2024-0001` |
| `invoice_date` | `date` | Date of invoice issuance |
| `financial_year` | `str` | Indian fiscal year (e.g. `2024-25`) |
| `tax_period` | `str` | Filing period in `YYYY-MM` format (e.g. `2024-07`) |
| `taxable_value` | `Decimal` | Base value of goods / services before tax |
| `cgst` | `Decimal` | Central Goods and Services Tax amount |
| `sgst` | `Decimal` | State Goods and Services Tax amount |
| `igst` | `Decimal` | Integrated Goods and Services Tax amount |
| `total_tax` | `Decimal` | Total tax ($CGST + SGST + IGST$) |
| `invoice_value` | `Decimal` | Total gross payable ($Taxable + TotalTax$) |
| `hsn_code` | `str` | 4 to 8 digit Harmonized System of Nomenclature code |
| `supply_type` | `SupplyType` | `INTRA_STATE` or `INTER_STATE` |
| `data_source` | `DataSource` | `public`, `synthetic`, or `derived` |
| `synthetic_profile` | `Optional[str]` | Originating behavioral profile code |
| `anomaly_type` | `Optional[str]` | Injected anomaly class if applicable |
| `anomaly_severity`| `Optional[str]` | `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL` |
| `is_duplicate` | `bool` | True if flagged as duplicate/near-duplicate |

---

### 2.3. Filing (`backend/data/schema.py`)
Represents statutory return filings per vendor per tax period.

| Field | Type | Description |
| :--- | :--- | :--- |
| `vendor_id` | `str` | Supplier vendor ID |
| `tax_period` | `str` | Filing period `YYYY-MM` |
| `gstr1_filed` | `bool` | Whether supplier filed outward supply return GSTR-1 |
| `gstr1_filing_date`| `Optional[date]` | Actual filing date (statutory deadline: 11th) |
| `gstr3b_filed` | `bool` | Whether supplier filed summary return GSTR-3B (tax remitted) |
| `gstr3b_filing_date`| `Optional[date]` | Actual payment date (statutory deadline: 20th) |
| `filing_delay_days`| `int` | Delay past statutory cutoff in days |

---

### 2.4. Reconciliation (`backend/data/schema.py`)
Multi-source reconciliation record linking supplier and buyer returns.

| Field | Type | Description |
| :--- | :--- | :--- |
| `invoice_id` | `str` | Target invoice identifier |
| `vendor_id` | `str` | Vendor ID |
| `tax_period` | `str` | Tax period `YYYY-MM` |
| `gstr1_present` | `bool` | Reported in supplier's GSTR-1 return |
| `gstr2b_present` | `bool` | Auto-populated in buyer's GSTR-2B inward statement |
| `purchase_register_present` | `bool` | Recorded in buyer's accounting books |
| `tax_amount_match` | `bool` | Declared tax matches calculated tax |
| `taxable_value_match` | `bool` | Declared taxable value matches books |
| `hsn_match` | `bool` | HSN/SAC code classification matches |
| `date_match` | `bool` | Invoice date aligned across reporting periods |
| `einvoice_present` | `bool` | Covered by valid e-Invoice Invoice Reference Number (IRN) |
| `ewaybill_present` | `bool` | Covered by valid electronic way bill |
| `reconciliation_status` | `ReconciliationStatus`| `Matched`, `Missing in GSTR-1`, `Tax Amount Mismatch`, etc. |
| `discrepancy_amount` | `Decimal` | Ineligible ITC or exposure amount |

---

## 3. GST Jurisdiction & Tax Calculation Logic

1. **Intra-State Supplies**:
   - Condition: $State_{Supplier} = State_{Buyer}$ (e.g. Karnataka to Karnataka)
   - $IGST = ₹0.00$
   - $CGST = \frac{TotalTax}{2}$, $SGST = TotalTax - CGST$ (allowing 1-paisa rounding splits for odd paise totals).
2. **Inter-State Supplies**:
   - Condition: $State_{Supplier} \neq State_{Buyer}$ (e.g. Maharashtra to Karnataka)
   - $CGST = ₹0.00$, $SGST = ₹0.00$
   - $IGST = TotalTax$
