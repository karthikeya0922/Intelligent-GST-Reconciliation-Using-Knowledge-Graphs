// ============================================================
// Mock Data for Intelligent GST Reconciliation Dashboard
// Realistic Indian GST data with GSTINs, HSN codes, INR amounts
// ============================================================

export const vendors = [
  { id: 'V001', gstin: '29AABCU9603R1ZM', name: 'Tata Steel Ltd', state: 'Karnataka', riskScore: 0.12, status: 'Compliant', totalTransactions: 245, missedFilings: 0, avgDaysLate: 0 },
  { id: 'V002', gstin: '27AADCB2230M1ZT', name: 'Bajaj Auto Ltd', state: 'Maharashtra', riskScore: 0.18, status: 'Compliant', totalTransactions: 189, missedFilings: 0, avgDaysLate: 1 },
  { id: 'V003', gstin: '33AABCT1332L1ZN', name: 'TVS Motor Company', state: 'Tamil Nadu', riskScore: 0.35, status: 'Review', totalTransactions: 156, missedFilings: 1, avgDaysLate: 3 },
  { id: 'V004', gstin: '06AABCM9407D1ZS', name: 'Mahindra & Mahindra', state: 'Haryana', riskScore: 0.22, status: 'Compliant', totalTransactions: 312, missedFilings: 0, avgDaysLate: 0 },
  { id: 'V005', gstin: '36AAACH7409R1ZK', name: 'Hyderabad Steels Pvt', state: 'Telangana', riskScore: 0.78, status: 'High Risk', totalTransactions: 67, missedFilings: 4, avgDaysLate: 12 },
  { id: 'V006', gstin: '19AABCR1718E1ZL', name: 'Reliance Industries', state: 'West Bengal', riskScore: 0.08, status: 'Compliant', totalTransactions: 534, missedFilings: 0, avgDaysLate: 0 },
  { id: 'V007', gstin: '07AABCI8490K1ZU', name: 'Infosys Ltd', state: 'Delhi', riskScore: 0.15, status: 'Compliant', totalTransactions: 421, missedFilings: 0, avgDaysLate: 0 },
  { id: 'V008', gstin: '32AABCW4531R1ZA', name: 'Wipro Technologies', state: 'Kerala', riskScore: 0.42, status: 'Review', totalTransactions: 198, missedFilings: 2, avgDaysLate: 5 },
  { id: 'V009', gstin: '24AABCL3580N1ZP', name: 'Larsen & Toubro', state: 'Gujarat', riskScore: 0.19, status: 'Compliant', totalTransactions: 367, missedFilings: 0, avgDaysLate: 1 },
  { id: 'V010', gstin: '09AABCS1429B1ZE', name: 'SunPharma Industries', state: 'Uttar Pradesh', riskScore: 0.65, status: 'High Risk', totalTransactions: 89, missedFilings: 3, avgDaysLate: 8 },
  { id: 'V011', gstin: '29AABCH1234M1ZQ', name: 'HCL Technologies', state: 'Karnataka', riskScore: 0.11, status: 'Compliant', totalTransactions: 276, missedFilings: 0, avgDaysLate: 0 },
  { id: 'V012', gstin: '27AABCD5678N1ZR', name: 'Deepak Nitrite Ltd', state: 'Maharashtra', riskScore: 0.55, status: 'Review', totalTransactions: 143, missedFilings: 2, avgDaysLate: 6 },
  { id: 'V013', gstin: '33AABCE9012P1ZS', name: 'EID Parry India', state: 'Tamil Nadu', riskScore: 0.72, status: 'High Risk', totalTransactions: 54, missedFilings: 5, avgDaysLate: 15 },
  { id: 'V014', gstin: '06AABCF3456Q1ZT', name: 'Federal-Mogul Goetze', state: 'Haryana', riskScore: 0.28, status: 'Compliant', totalTransactions: 201, missedFilings: 1, avgDaysLate: 2 },
  { id: 'V015', gstin: '36AABCG7890R1ZU', name: 'Granules India Ltd', state: 'Telangana', riskScore: 0.31, status: 'Review', totalTransactions: 178, missedFilings: 1, avgDaysLate: 4 },
  { id: 'V016', gstin: '19AABCH2345S1ZV', name: 'Hindustan Unilever', state: 'West Bengal', riskScore: 0.09, status: 'Compliant', totalTransactions: 489, missedFilings: 0, avgDaysLate: 0 },
  { id: 'V017', gstin: '07AABCI6789T1ZW', name: 'ITC Limited', state: 'Delhi', riskScore: 0.14, status: 'Compliant', totalTransactions: 356, missedFilings: 0, avgDaysLate: 0 },
  { id: 'V018', gstin: '32AABCJ1234U1ZX', name: 'Jubilant Foodworks', state: 'Kerala', riskScore: 0.82, status: 'High Risk', totalTransactions: 42, missedFilings: 6, avgDaysLate: 18 },
  { id: 'V019', gstin: '24AABCK5678V1ZY', name: 'Kotak Mahindra Bank', state: 'Gujarat', riskScore: 0.16, status: 'Compliant', totalTransactions: 298, missedFilings: 0, avgDaysLate: 1 },
  { id: 'V020', gstin: '09AABCL9012W1ZZ', name: 'Lupin Limited', state: 'Uttar Pradesh', riskScore: 0.48, status: 'Review', totalTransactions: 167, missedFilings: 2, avgDaysLate: 7 },
];

export const invoices = [
  { id: 'INV-2025-001', vendorId: 'V005', vendorName: 'Hyderabad Steels Pvt', gstin: '36AAACH7409R1ZK', date: '2025-07-15', taxableAmount: 450000, cgst: 40500, sgst: 40500, igst: 0, totalTax: 81000, total: 531000, hsn: '7208', period: '2025-07', gstr1Reported: false, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Missing in GSTR-1', riskLevel: 'High' },
  { id: 'INV-2025-002', vendorId: 'V001', vendorName: 'Tata Steel Ltd', gstin: '29AABCU9603R1ZM', date: '2025-07-18', taxableAmount: 1200000, cgst: 108000, sgst: 108000, igst: 0, totalTax: 216000, total: 1416000, hsn: '7210', period: '2025-07', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Matched', riskLevel: 'Low' },
  { id: 'INV-2025-003', vendorId: 'V010', vendorName: 'SunPharma Industries', gstin: '09AABCS1429B1ZE', date: '2025-07-20', taxableAmount: 320000, cgst: 19200, sgst: 19200, igst: 0, totalTax: 38400, total: 358400, hsn: '3004', period: '2025-07', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: false, matchStatus: 'Tax Amount Mismatch', riskLevel: 'Medium' },
  { id: 'INV-2025-004', vendorId: 'V013', vendorName: 'EID Parry India', gstin: '33AABCE9012P1ZS', date: '2025-07-22', taxableAmount: 780000, cgst: 70200, sgst: 70200, igst: 0, totalTax: 140400, total: 920400, hsn: '1701', period: '2025-07', gstr1Reported: false, gstr2bReported: true, eInvoice: false, eWayBill: true, matchStatus: 'Missing in GSTR-1', riskLevel: 'High' },
  { id: 'INV-2025-005', vendorId: 'V006', vendorName: 'Reliance Industries', gstin: '19AABCR1718E1ZL', date: '2025-07-25', taxableAmount: 2500000, cgst: 225000, sgst: 225000, igst: 0, totalTax: 450000, total: 2950000, hsn: '2710', period: '2025-07', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Matched', riskLevel: 'Low' },
  { id: 'INV-2025-006', vendorId: 'V003', vendorName: 'TVS Motor Company', gstin: '33AABCT1332L1ZN', date: '2025-07-28', taxableAmount: 180000, cgst: 16200, sgst: 16200, igst: 0, totalTax: 32400, total: 212400, hsn: '8711', period: '2025-07', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'HSN Mismatch', riskLevel: 'Medium' },
  { id: 'INV-2025-007', vendorId: 'V018', vendorName: 'Jubilant Foodworks', gstin: '32AABCJ1234U1ZX', date: '2025-08-01', taxableAmount: 95000, cgst: 8550, sgst: 8550, igst: 0, totalTax: 17100, total: 112100, hsn: '2106', period: '2025-08', gstr1Reported: false, gstr2bReported: true, eInvoice: false, eWayBill: false, matchStatus: 'Missing in GSTR-1', riskLevel: 'High' },
  { id: 'INV-2025-008', vendorId: 'V007', vendorName: 'Infosys Ltd', gstin: '07AABCI8490K1ZU', date: '2025-08-03', taxableAmount: 3500000, cgst: 315000, sgst: 315000, igst: 0, totalTax: 630000, total: 4130000, hsn: '9983', period: '2025-08', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: false, matchStatus: 'Matched', riskLevel: 'Low' },
  { id: 'INV-2025-009', vendorId: 'V012', vendorName: 'Deepak Nitrite Ltd', gstin: '27AABCD5678N1ZR', date: '2025-08-05', taxableAmount: 560000, cgst: 50400, sgst: 50400, igst: 0, totalTax: 100800, total: 660800, hsn: '2914', period: '2025-08', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Tax Amount Mismatch', riskLevel: 'Medium' },
  { id: 'INV-2025-010', vendorId: 'V002', vendorName: 'Bajaj Auto Ltd', gstin: '27AADCB2230M1ZT', date: '2025-08-08', taxableAmount: 890000, cgst: 80100, sgst: 80100, igst: 0, totalTax: 160200, total: 1050200, hsn: '8711', period: '2025-08', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Matched', riskLevel: 'Low' },
  { id: 'INV-2025-011', vendorId: 'V005', vendorName: 'Hyderabad Steels Pvt', gstin: '36AAACH7409R1ZK', date: '2025-08-10', taxableAmount: 670000, cgst: 60300, sgst: 60300, igst: 0, totalTax: 120600, total: 790600, hsn: '7208', period: '2025-08', gstr1Reported: false, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Missing in GSTR-1', riskLevel: 'High' },
  { id: 'INV-2025-012', vendorId: 'V009', vendorName: 'Larsen & Toubro', gstin: '24AABCL3580N1ZP', date: '2025-08-12', taxableAmount: 1450000, cgst: 130500, sgst: 130500, igst: 0, totalTax: 261000, total: 1711000, hsn: '8429', period: '2025-08', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Matched', riskLevel: 'Low' },
  { id: 'INV-2025-013', vendorId: 'V020', vendorName: 'Lupin Limited', gstin: '09AABCL9012W1ZZ', date: '2025-08-15', taxableAmount: 230000, cgst: 13800, sgst: 13800, igst: 0, totalTax: 27600, total: 257600, hsn: '3004', period: '2025-08', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Late Filing', riskLevel: 'Medium' },
  { id: 'INV-2025-014', vendorId: 'V004', vendorName: 'Mahindra & Mahindra', gstin: '06AABCM9407D1ZS', date: '2025-08-18', taxableAmount: 1800000, cgst: 162000, sgst: 162000, igst: 0, totalTax: 324000, total: 2124000, hsn: '8703', period: '2025-08', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Matched', riskLevel: 'Low' },
  { id: 'INV-2025-015', vendorId: 'V015', vendorName: 'Granules India Ltd', gstin: '36AABCG7890R1ZU', date: '2025-08-20', taxableAmount: 410000, cgst: 24600, sgst: 24600, igst: 0, totalTax: 49200, total: 459200, hsn: '2933', period: '2025-08', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: false, matchStatus: 'E-Way Bill Missing', riskLevel: 'Medium' },
  { id: 'INV-2025-016', vendorId: 'V008', vendorName: 'Wipro Technologies', gstin: '32AABCW4531R1ZA', date: '2025-09-01', taxableAmount: 1750000, cgst: 157500, sgst: 157500, igst: 0, totalTax: 315000, total: 2065000, hsn: '9983', period: '2025-09', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: false, matchStatus: 'Tax Amount Mismatch', riskLevel: 'Medium' },
  { id: 'INV-2025-017', vendorId: 'V013', vendorName: 'EID Parry India', gstin: '33AABCE9012P1ZS', date: '2025-09-03', taxableAmount: 520000, cgst: 46800, sgst: 46800, igst: 0, totalTax: 93600, total: 613600, hsn: '1701', period: '2025-09', gstr1Reported: false, gstr2bReported: true, eInvoice: false, eWayBill: false, matchStatus: 'Missing in GSTR-1', riskLevel: 'High' },
  { id: 'INV-2025-018', vendorId: 'V011', vendorName: 'HCL Technologies', gstin: '29AABCH1234M1ZQ', date: '2025-09-05', taxableAmount: 2200000, cgst: 198000, sgst: 198000, igst: 0, totalTax: 396000, total: 2596000, hsn: '9983', period: '2025-09', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: false, matchStatus: 'Matched', riskLevel: 'Low' },
  { id: 'INV-2025-019', vendorId: 'V010', vendorName: 'SunPharma Industries', gstin: '09AABCS1429B1ZE', date: '2025-09-08', taxableAmount: 145000, cgst: 8700, sgst: 8700, igst: 0, totalTax: 17400, total: 162400, hsn: '3004', period: '2025-09', gstr1Reported: false, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Missing in GSTR-1', riskLevel: 'High' },
  { id: 'INV-2025-020', vendorId: 'V016', vendorName: 'Hindustan Unilever', gstin: '19AABCH2345S1ZV', date: '2025-09-10', taxableAmount: 980000, cgst: 88200, sgst: 88200, igst: 0, totalTax: 176400, total: 1156400, hsn: '3401', period: '2025-09', gstr1Reported: true, gstr2bReported: true, eInvoice: true, eWayBill: true, matchStatus: 'Matched', riskLevel: 'Low' },
];

export const mismatches = invoices.filter(inv => inv.matchStatus !== 'Matched');

export const mismatchTypes = [
  { type: 'Missing in GSTR-1', count: 6, totalTax: 452400, color: '#ef4444' },
  { type: 'Tax Amount Mismatch', count: 3, totalTax: 454200, color: '#f59e0b' },
  { type: 'HSN Mismatch', count: 1, totalTax: 32400, color: '#8b5cf6' },
  { type: 'Late Filing', count: 1, totalTax: 27600, color: '#3b82f6' },
  { type: 'E-Way Bill Missing', count: 1, totalTax: 49200, color: '#06b6d4' },
];

export const monthlyITCRisk = [
  { month: 'Jan 2025', atRisk: 320000, total: 4500000 },
  { month: 'Feb 2025', atRisk: 180000, total: 3800000 },
  { month: 'Mar 2025', atRisk: 450000, total: 5200000 },
  { month: 'Apr 2025', atRisk: 280000, total: 4100000 },
  { month: 'May 2025', atRisk: 520000, total: 4900000 },
  { month: 'Jun 2025', atRisk: 390000, total: 5500000 },
  { month: 'Jul 2025', atRisk: 621400, total: 6200000 },
  { month: 'Aug 2025', atRisk: 448200, total: 5800000 },
  { month: 'Sep 2025', atRisk: 507000, total: 5400000 },
];

export const gstrReturns = [
  { type: 'GSTR-1', period: '2025-07', totalInvoices: 156, totalTaxable: 8500000, totalTax: 1530000, filedDate: '2025-08-11', status: 'Filed' },
  { type: 'GSTR-2B', period: '2025-07', totalInvoices: 162, totalTaxable: 9200000, totalTax: 1656000, filedDate: '2025-08-14', status: 'Auto-generated' },
  { type: 'GSTR-3B', period: '2025-07', totalInvoices: null, totalTaxable: 8500000, totalTax: 1530000, filedDate: '2025-08-20', status: 'Filed' },
  { type: 'GSTR-1', period: '2025-08', totalInvoices: 178, totalTaxable: 9800000, totalTax: 1764000, filedDate: '2025-09-11', status: 'Filed' },
  { type: 'GSTR-2B', period: '2025-08', totalInvoices: 185, totalTaxable: 10500000, totalTax: 1890000, filedDate: '2025-09-14', status: 'Auto-generated' },
  { type: 'GSTR-3B', period: '2025-08', totalInvoices: null, totalTaxable: 9800000, totalTax: 1764000, filedDate: '2025-09-20', status: 'Filed' },
];

export const riskFeatureImportance = [
  { feature: 'Past Mismatch Count', importance: 0.28 },
  { feature: 'Cumulative Tax at Risk', importance: 0.22 },
  { feature: 'Filing Delay (days)', importance: 0.18 },
  { feature: 'Graph Centrality Score', importance: 0.12 },
  { feature: 'Transaction Volume', importance: 0.08 },
  { feature: 'Community Cluster ID', importance: 0.06 },
  { feature: 'E-Invoice Compliance', importance: 0.04 },
  { feature: 'State Location Factor', importance: 0.02 },
];

export const auditExplanations = {
  'INV-2025-001': {
    summary: "Invoice INV-2025-001 (₹4,50,000 taxable, ₹81,000 tax) claimed as purchase by your entity under GSTR-2B for July 2025 is flagged because the supplier Hyderabad Steels Pvt (GSTIN: 36AAACH7409R1ZK) has NOT reported this invoice in their GSTR-1 for the same period.",
    evidence: [
      "Invoice INV-2025-001 appears in your GSTR-2B (auto-populated) for July 2025",
      "Cross-reference with Vendor's GSTR-1 for July 2025: NO matching entry found",
      "e-Invoice IRN was generated (valid), but vendor failed to include it in their return",
      "Vendor Hyderabad Steels has a compliance risk score of 0.78 (High Risk)",
      "This vendor has 4 missed filings in the past 12 months"
    ],
    recommendation: "ITC of ₹81,000 is at risk of disallowance under Section 16(2)(aa) of CGST Act. Recommend contacting the vendor to file an amendment or withholding ITC claim until GSTR-1 is updated.",
    graphPath: "Your Entity → GSTR-2B (Jul-25) → INV-2025-001 → [MISSING: Vendor GSTR-1] → Hyderabad Steels Pvt"
  },
  'INV-2025-003': {
    summary: "Invoice INV-2025-003 (₹3,20,000 taxable) from SunPharma Industries shows a tax amount discrepancy between GSTR-1 and GSTR-2B entries. The vendor reported ₹36,000 total tax in GSTR-1 vs ₹38,400 in your GSTR-2B.",
    evidence: [
      "GSTR-2B shows CGST: ₹19,200 + SGST: ₹19,200 = ₹38,400",
      "Vendor's GSTR-1 shows CGST: ₹18,000 + SGST: ₹18,000 = ₹36,000",
      "Tax rate discrepancy: 12% applied in GSTR-2B vs. 11.25% in GSTR-1",
      "HSN code 3004 (pharmaceutical products) applicable rate is 12% GST",
      "Vendor may have applied incorrect tax rate in their filing"
    ],
    recommendation: "Difference of ₹2,400 needs reconciliation. The correct rate for HSN 3004 is 12%. Vendor should file an amendment to GSTR-1 to correct the tax amount.",
    graphPath: "Your Entity → GSTR-2B → INV-2025-003 (₹38,400 tax) → [MISMATCH] → Vendor GSTR-1 (₹36,000 tax) → SunPharma Industries"
  },
  'INV-2025-004': {
    summary: "Invoice INV-2025-004 (₹7,80,000 taxable, ₹1,40,400 tax) from EID Parry India is completely absent from the vendor's GSTR-1 filing for July 2025. Additionally, no e-Invoice IRN was generated for this transaction.",
    evidence: [
      "Invoice appears in your GSTR-2B for July 2025",
      "EID Parry's GSTR-1 for July 2025: NO matching invoice found",
      "No e-Invoice IRN exists for this invoice number",
      "e-Way Bill was generated (EWB-2025-04892), confirming goods movement",
      "Vendor EID Parry has a risk score of 0.72 (High Risk) with 5 missed filings"
    ],
    recommendation: "This represents a significant ITC risk of ₹1,40,400. The absence of both GSTR-1 entry and e-Invoice raises compliance concerns. Escalate to vendor management for immediate resolution. Consider filing a complaint on the GST portal.",
    graphPath: "Your Entity → GSTR-2B → INV-2025-004 → [MISSING: e-Invoice] → [MISSING: Vendor GSTR-1] → EID Parry India"
  },
  'INV-2025-006': {
    summary: "Invoice INV-2025-006 from TVS Motor Company has an HSN code mismatch. Your purchase register records HSN 8711 (motorcycles) but the vendor's GSTR-1 reports HSN 8714 (parts and accessories).",
    evidence: [
      "Your GSTR-2B entry: HSN 8711 - Motorcycles (including mopeds)",
      "Vendor's GSTR-1 entry: HSN 8714 - Parts and accessories of vehicles",
      "Tax amount matches: ₹32,400 in both records",
      "HSN classification affects applicable tax rate brackets",
      "TVS Motor has a moderate risk score of 0.35"
    ],
    recommendation: "HSN mismatch may not affect ITC eligibility if tax amounts match, but needs correction for accurate reporting. Request vendor to verify correct HSN classification.",
    graphPath: "Your Entity → GSTR-2B (HSN:8711) → INV-2025-006 → [HSN MISMATCH] → Vendor GSTR-1 (HSN:8714) → TVS Motor"
  },
};

// Knowledge Graph data for visualization
export const graphData = {
  nodes: [
    // Vendor nodes
    { id: 'v1', label: 'Tata Steel Ltd', group: 'vendor', gstin: '29AABCU9603R1ZM', risk: 0.12 },
    { id: 'v2', label: 'Hyderabad Steels', group: 'vendor', gstin: '36AAACH7409R1ZK', risk: 0.78 },
    { id: 'v3', label: 'SunPharma', group: 'vendor', gstin: '09AABCS1429B1ZE', risk: 0.65 },
    { id: 'v4', label: 'Reliance Ind.', group: 'vendor', gstin: '19AABCR1718E1ZL', risk: 0.08 },
    { id: 'v5', label: 'EID Parry', group: 'vendor', gstin: '33AABCE9012P1ZS', risk: 0.72 },
    { id: 'v6', label: 'Infosys Ltd', group: 'vendor', gstin: '07AABCI8490K1ZU', risk: 0.15 },
    { id: 'v7', label: 'TVS Motor', group: 'vendor', gstin: '33AABCT1332L1ZN', risk: 0.35 },
    { id: 'v8', label: 'Jubilant Foods', group: 'vendor', gstin: '32AABCJ1234U1ZX', risk: 0.82 },
    // Invoice nodes
    { id: 'i1', label: 'INV-001', group: 'invoice', amount: 531000, status: 'flagged' },
    { id: 'i2', label: 'INV-002', group: 'invoice', amount: 1416000, status: 'matched' },
    { id: 'i3', label: 'INV-003', group: 'invoice', amount: 358400, status: 'flagged' },
    { id: 'i4', label: 'INV-004', group: 'invoice', amount: 920400, status: 'flagged' },
    { id: 'i5', label: 'INV-005', group: 'invoice', amount: 2950000, status: 'matched' },
    { id: 'i6', label: 'INV-006', group: 'invoice', amount: 212400, status: 'flagged' },
    { id: 'i7', label: 'INV-007', group: 'invoice', amount: 112100, status: 'flagged' },
    { id: 'i8', label: 'INV-008', group: 'invoice', amount: 4130000, status: 'matched' },
    // GSTR nodes
    { id: 'g1', label: 'GSTR-1 Jul', group: 'gstr', type: 'GSTR-1', period: '2025-07' },
    { id: 'g2', label: 'GSTR-2B Jul', group: 'gstr', type: 'GSTR-2B', period: '2025-07' },
    { id: 'g3', label: 'GSTR-3B Jul', group: 'gstr', type: 'GSTR-3B', period: '2025-07' },
    { id: 'g4', label: 'GSTR-1 Aug', group: 'gstr', type: 'GSTR-1', period: '2025-08' },
    { id: 'g5', label: 'GSTR-2B Aug', group: 'gstr', type: 'GSTR-2B', period: '2025-08' },
    // e-Invoice nodes
    { id: 'e1', label: 'IRN-001', group: 'einvoice', status: 'valid' },
    { id: 'e2', label: 'IRN-002', group: 'einvoice', status: 'valid' },
    { id: 'e3', label: 'IRN-005', group: 'einvoice', status: 'valid' },
    // E-Way Bill nodes
    { id: 'w1', label: 'EWB-001', group: 'ewaybill', status: 'active' },
    { id: 'w2', label: 'EWB-004', group: 'ewaybill', status: 'active' },
  ],
  links: [
    // Vendor -> Invoice (ISSUED_INVOICE)
    { source: 'v2', target: 'i1', label: 'ISSUED_INVOICE', type: 'issued' },
    { source: 'v1', target: 'i2', label: 'ISSUED_INVOICE', type: 'issued' },
    { source: 'v3', target: 'i3', label: 'ISSUED_INVOICE', type: 'issued' },
    { source: 'v5', target: 'i4', label: 'ISSUED_INVOICE', type: 'issued' },
    { source: 'v4', target: 'i5', label: 'ISSUED_INVOICE', type: 'issued' },
    { source: 'v7', target: 'i6', label: 'ISSUED_INVOICE', type: 'issued' },
    { source: 'v8', target: 'i7', label: 'ISSUED_INVOICE', type: 'issued' },
    { source: 'v6', target: 'i8', label: 'ISSUED_INVOICE', type: 'issued' },
    // Invoice -> GSTR (REPORTED_IN)
    { source: 'i1', target: 'g2', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i2', target: 'g1', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i2', target: 'g2', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i3', target: 'g1', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i3', target: 'g2', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i4', target: 'g2', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i5', target: 'g1', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i5', target: 'g2', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i6', target: 'g1', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i6', target: 'g2', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i7', target: 'g5', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i8', target: 'g4', label: 'REPORTED_IN', type: 'reported' },
    { source: 'i8', target: 'g5', label: 'REPORTED_IN', type: 'reported' },
    // GSTR -> GSTR-3B (SUMMARIZED_IN)
    { source: 'g1', target: 'g3', label: 'SUMMARIZED_IN', type: 'summary' },
    { source: 'g2', target: 'g3', label: 'SUMMARIZED_IN', type: 'summary' },
    // Invoice -> e-Invoice (ELECTRONIC_VERSION)
    { source: 'i1', target: 'e1', label: 'ELECTRONIC_VERSION', type: 'einvoice' },
    { source: 'i2', target: 'e2', label: 'ELECTRONIC_VERSION', type: 'einvoice' },
    { source: 'i5', target: 'e3', label: 'ELECTRONIC_VERSION', type: 'einvoice' },
    // Invoice -> E-Way Bill (COVERS_SHIPMENT)
    { source: 'i1', target: 'w1', label: 'COVERS_SHIPMENT', type: 'ewaybill' },
    { source: 'i4', target: 'w2', label: 'COVERS_SHIPMENT', type: 'ewaybill' },
  ]
};

// KPI summary data
export const kpiData = {
  totalInvoices: 520,
  totalMismatches: 12,
  atRiskITC: 1576800,
  vendorsMonitored: 20,
  matchRate: 94.2,
  avgResolutionDays: 4.2,
  highRiskVendors: 4,
  pendingReconciliations: 8,
};

export const recentAlerts = [
  { id: 1, type: 'critical', message: 'Hyderabad Steels has 2 new unmatched invoices totaling ₹2,01,600 in tax', time: '2 hours ago', icon: '🔴' },
  { id: 2, type: 'warning', message: 'EID Parry India GSTR-1 for Sep 2025 is 15 days overdue', time: '5 hours ago', icon: '🟡' },
  { id: 3, type: 'info', message: 'Quarterly reconciliation report generated for Q2 2025', time: '1 day ago', icon: '🔵' },
  { id: 4, type: 'warning', message: 'Tax amount mismatch detected for Wipro Technologies INV-2025-016', time: '1 day ago', icon: '🟡' },
  { id: 5, type: 'success', message: 'Vendor risk model retrained with 98.3% accuracy', time: '2 days ago', icon: '🟢' },
  { id: 6, type: 'critical', message: 'Jubilant Foodworks compliance score dropped below threshold', time: '3 days ago', icon: '🔴' },
];

export const complianceTrend = [
  { month: 'Jan', compliant: 85, review: 10, highRisk: 5 },
  { month: 'Feb', compliant: 87, review: 9, highRisk: 4 },
  { month: 'Mar', compliant: 82, review: 12, highRisk: 6 },
  { month: 'Apr', compliant: 88, review: 8, highRisk: 4 },
  { month: 'May', compliant: 84, review: 11, highRisk: 5 },
  { month: 'Jun', compliant: 86, review: 9, highRisk: 5 },
  { month: 'Jul', compliant: 80, review: 12, highRisk: 8 },
  { month: 'Aug', compliant: 83, review: 10, highRisk: 7 },
  { month: 'Sep', compliant: 85, review: 10, highRisk: 5 },
];
