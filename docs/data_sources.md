# External Data Sources Discovery & Evaluation

This document evaluates publicly available business transaction and invoice datasets for integration into the GST ReconcileAI hybrid dataset pipeline.

> [!IMPORTANT]
> **Disclaimer on Taxpayer Privacy & Data Provenance**  
> Under Section 158 of the Central Goods and Services Tax (CGST) Act, 2017, genuine GST return filings and taxpayer disclosures are strictly confidential. Authentic transaction-level GST datasets containing non-anonymized real taxpayer filings are not legally permitted to be published or redistributed without official statutory authorization.  
> 
> Therefore, our hybrid pipeline uses **publicly available commercial transaction datasets** to reflect genuine enterprise transaction characteristics (item pricing, quantity distributions, invoice sizes, customer/vendor relationships, and seasonality), and maps them via modular adapters into our canonical GST schema. Controlled synthetic GST filings (GSTR-1, GSTR-2B, GSTR-3B, e-Way Bills, e-Invoices) are then deterministically generated and linked to simulate statutory compliance scenarios.

---

## 1. Candidate Datasets

### Dataset A: UCI Machine Learning Repository — Online Retail Dataset

| Attribute | Details |
| :--- | :--- |
| **Dataset Name** | Online Retail II / Online Retail Data Set |
| **Source URL** | [UCI ML Repository - Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) |
| **License** | Creative Commons Attribution 4.0 International (CC BY 4.0) |
| **Number of Records** | 541,909 transactions across 4,372 unique customers and 38 countries (2010–2011) |
| **Available Fields** | `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country` |
| **Relevance to GST** | Excellent real-world invoice line item structure, quantity distributions, realistic enterprise purchasing patterns, unit pricing, return/cancellation events (credit notes indicated by 'C' prefix). |
| **Limitations** | Pre-dates Indian GST (2017). Does not contain GSTINs, HSN codes, or Indian state jurisdictions. Prices in GBP rather than INR. |
| **Transformations Required** | 1. Group line items by `InvoiceNo` to compute aggregate taxable amounts.<br>2. Map CustomerID and synthetic suppliers into valid 15-character GSTINs.<br>3. Map product descriptions/StockCode into 4-to-8 digit HSN codes.<br>4. Convert currency to INR with standard price scaling.<br>5. Compute CGST, SGST, IGST based on supplier/buyer state residency (intra-state vs inter-state). |
| **Redistribution Allowed?** | Yes, with attribution under CC BY 4.0. |
| **Commit Raw to Git?** | **No**. The raw CSV is ~45MB. Provide a scripted automated downloader and sample extract instead. |

---

### Dataset B: Kaggle B2B Electronic Invoicing / Payments Dataset

| Attribute | Details |
| :--- | :--- |
| **Dataset Name** | Invoice Payment Status & B2B Invoicing Dataset |
| **Source URL** | [Kaggle B2B Invoice Dataset](https://www.kaggle.com/datasets) (e.g. B2B Invoice Payment Forecasting) |
| **License** | Open Database License (ODbL) / Database Contents License |
| **Number of Records** | ~50,000–100,000 invoices |
| **Available Fields** | `business_code`, `cust_number`, `name_customer`, `clear_date`, `buisness_year`, `doc_id`, `posting_date`, `document_create_date`, `due_in_date`, `invoice_currency`, `total_open_amount`, `baseline_create_date` |
| **Relevance to GST** | Provides realistic corporate payment delays, credit terms, payment default cycles, and buyer-seller transaction volumes. |
| **Limitations** | Lacks tax itemization (CGST/SGST/IGST breakdown), does not have item-level HSN codes. |
| **Transformations Required** | Synthesize tax breakdown based on Indian GST tax slab rates (5%, 12%, 18%, 28%) and determine filing delay correlation with payment delays. |
| **Redistribution Allowed?** | Varies by Kaggle author; redistribution of raw files directly is discouraged. |
| **Commit Raw to Git?** | **No**. |

---

### Dataset C: Open Government Data (OGD) Platform India (data.gov.in)

| Attribute | Details |
| :--- | :--- |
| **Dataset Name** | GST Collections and State-wise Return Filing Aggregates |
| **Source URL** | [data.gov.in](https://data.gov.in/) |
| **License** | National Data Sharing and Accessibility Policy (NDSAP) / Government Open Data License - India |
| **Number of Records** | Monthly state-level aggregate figures (2017–present) |
| **Available Fields** | `state_code`, `state_name`, `month`, `year`, `total_collections_cr`, `cgst_cr`, `sgst_cr`, `igst_cr`, `cess_cr`, `filing_compliance_percent` |
| **Relevance to GST** | Provides empirical state-level compliance priors (e.g. filing timeliness and compliance proportions across Maharashtra, Karnataka, Gujarat, etc.), which we use to parameterize our state risk factors and profile distributions. |
| **Limitations** | Aggregated at state/month level; zero entity-level or invoice-level records. |
| **Transformations Required** | Extract state-level filing discipline priors to calibrate the synthetic behavioral profiles. |
| **Redistribution Allowed?** | Yes, under Government Open Data License - India. |
| **Commit Raw to Git?** | Yes, aggregated metadata and distribution parameters are incorporated into codebase configuration. |

---

## 2. Selection & Strategy for Hybrid Pipeline

To build a research-grade hybrid dataset while respecting licensing, privacy, and technical constraints:

1. **Primary Public Base**:
   We implement a modular public adapter (`backend/data/public/adapters/retail_invoice.py`) tailored to invoice/transaction structures exemplified by the UCI Retail schema.
2. **Deterministic Data Normalization**:
   The adapter normalizes external transactions into the canonical GST `Invoice` schema, assigning valid Indian state codes, synthetic GSTINs, and calculating consistent intra/inter-state tax breakdowns.
3. **Controlled Synthetic Injection**:
   Our synthetic engine injects GST-specific compliance events (GSTR-1 filing dates, GSTR-2B inward supplies, GSTR-3B tax remittal, e-Invoicing IRNs, and e-Way Bills) on top of both public and synthetic base transactions.
4. **Data Download Helper**:
   `backend/data/public/loader.py` provides download automation with SHA-256 integrity verification, while `data/sample/` stores a minimal, repository-safe curated hybrid sample for testing and continuous integration without inflating the Git history.
