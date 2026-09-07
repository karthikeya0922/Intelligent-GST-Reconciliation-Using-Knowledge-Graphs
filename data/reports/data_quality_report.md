# Dataset Quality & Integrity Report
*Generated on 2026-09-07T14:55:50.690055 (Seed: 42)*

## 1. Dataset Overview
- **Total Vendors**: 2,015
- **Total Invoices**: 168,213
- **Public Records**: 50
- **Synthetic Records**: 168,163
- **Tax Periods Simulated**: 24
- **Feature Rows Generated**: 46,345

## 2. Validation & Quality Checks
- **Overall Pipeline Validation Status**: ✅ PASSED
- **Invoice Arithmetic Errors**: 0
- **Jurisdiction / Tax Routing Errors**: 0
- **Temporal Chronology Errors**: 0
- **ITC Exposure Inconsistencies**: 0
- **Accidental Duplicates Detected**: 0
- **Intentional Anomaly Duplicates**: 1790

## 3. Injected Anomalies Breakdown
| Anomaly Type | Count |
| :--- | :--- |
| `DUPLICATE_INVOICE` | 1,059 |
| `LATE_FILING` | 9,884 |
| `MISSING_EINVOICE` | 14,898 |
| `MISSING_EWAY_BILL` | 11,136 |
| `MISSING_GSTR1` | 3,609 |
| `MISSING_GSTR3B` | 3,837 |
| `NEAR_DUPLICATE_INVOICE` | 1,085 |
| `TAXABLE_VALUE_MISMATCH` | 8,283 |
| `TAX_MISMATCH` | 13,027 |

## 4. Vendor Behavioral Profiles
| Profile Code | Vendor Count | Description |
| :--- | :--- | :--- |
| **A** | 1119 | Compliant Vendor |
| **B** | 298 | Occasional Mismatch |
| **C** | 160 | Chronic Mismatch |
| **D** | 184 | Late Filer |
| **E** | 101 | Missing-Return Vendor |
| **F** | 49 | High ITC Exposure |
| **G** | 46 | Suspicious Network |
| **H** | 43 | Duplicate Generator |
| **PUBLIC** | 15 | Public External Supplier |

## 5. Future-Period Target Compliance Label Distribution
| Risk Label | Vendor-Period Count | Percentage |
| :--- | :--- | :--- |
| **High** | 4,144 | 8.9% |
| **Low** | 34,218 | 73.8% |
| **Medium** | 7,983 | 17.2% |

## 6. Temporal Train / Validation / Test Splits
| Split | Rows | Low Risk (%) | Medium Risk (%) | High Risk (%) |
| :--- | :--- | :--- | :--- | :--- |
| **Train** | 30,225 | 74.2% | 16.8% | 9.0% |
| **Validation** | 8,060 | 73.5% | 17.4% | 9.0% |
| **Test** | 8,060 | 73.0% | 18.5% | 8.6% |

> **Integrity Assurance**: Zero future-period metrics were accessible or utilized in the feature matrix columns.