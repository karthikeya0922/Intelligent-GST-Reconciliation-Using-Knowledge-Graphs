"""
Dedicated Anomaly Injection Engine for Synthetic GST Data.

Supports 13 controlled anomaly types across invoice, filing, and reconciliation layers:
- TAX_MISMATCH
- TAXABLE_VALUE_MISMATCH
- MISSING_GSTR1
- MISSING_GSTR2B
- MISSING_GSTR3B
- HSN_MISMATCH
- DATE_MISMATCH
- DUPLICATE_INVOICE
- NEAR_DUPLICATE_INVOICE
- MISSING_EINVOICE
- MISSING_EWAY_BILL
- LATE_FILING
- UNUSUAL_TRANSACTION

Each injected anomaly logs its type, severity, affected fields, and detailed statutory explanation.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
import random
from typing import List, Dict, Any, Optional, Tuple

from backend.data.schema import (
    Invoice, Filing, Reconciliation, ReconciliationStatus, SupplyType, TWOPLACES
)


class AnomalyType(str, Enum):
    TAX_MISMATCH = "TAX_MISMATCH"
    TAXABLE_VALUE_MISMATCH = "TAXABLE_VALUE_MISMATCH"
    MISSING_GSTR1 = "MISSING_GSTR1"
    MISSING_GSTR2B = "MISSING_GSTR2B"
    MISSING_GSTR3B = "MISSING_GSTR3B"
    HSN_MISMATCH = "HSN_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    DUPLICATE_INVOICE = "DUPLICATE_INVOICE"
    NEAR_DUPLICATE_INVOICE = "NEAR_DUPLICATE_INVOICE"
    MISSING_EINVOICE = "MISSING_EINVOICE"
    MISSING_EWAY_BILL = "MISSING_EWAY_BILL"
    LATE_FILING = "LATE_FILING"
    UNUSUAL_TRANSACTION = "UNUSUAL_TRANSACTION"


class AnomalySeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class InjectedAnomalyRecord:
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    invoice_id: str
    vendor_id: str
    tax_period: str
    affected_fields: List[str]
    original_value: Any
    anomalous_value: Any
    explanation: str


class AnomalyEngine:
    """Injects controlled, domain-rich anomalies into synthetic invoices and filings."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.anomaly_log: List[InjectedAnomalyRecord] = []

    def inject_tax_mismatch(self, invoice: Invoice, discrepancy_pct: float = 0.15) -> Invoice:
        """Modifies tax amounts on invoice without adjusting taxable value (supplier math error)."""
        orig_tax = invoice.total_tax
        # Skew tax by discrepancy percentage
        multiplier = Decimal(str(1.0 + (discrepancy_pct if self.rng.random() > 0.5 else -discrepancy_pct)))
        new_tax = (orig_tax * multiplier).quantize(TWOPLACES)
        if new_tax == orig_tax:
            new_tax = orig_tax + Decimal("1500.00")

        diff = new_tax - orig_tax
        if invoice.supply_type == SupplyType.INTRA_STATE:
            half = (diff / Decimal("2.00")).quantize(TWOPLACES)
            invoice.cgst = (invoice.cgst + half).quantize(TWOPLACES)
            invoice.sgst = (invoice.sgst + (diff - half)).quantize(TWOPLACES)
        else:
            invoice.igst = (invoice.igst + diff).quantize(TWOPLACES)

        invoice.total_tax = new_tax
        invoice.invoice_value = (invoice.taxable_value + invoice.total_tax).quantize(TWOPLACES)
        invoice.anomaly_type = AnomalyType.TAX_MISMATCH.value
        invoice.anomaly_severity = AnomalySeverity.HIGH.value

        record = InjectedAnomalyRecord(
            anomaly_type=AnomalyType.TAX_MISMATCH,
            severity=AnomalySeverity.HIGH,
            invoice_id=invoice.invoice_id,
            vendor_id=invoice.vendor_id,
            tax_period=invoice.tax_period,
            affected_fields=["cgst", "sgst", "igst", "total_tax"],
            original_value=str(orig_tax),
            anomalous_value=str(new_tax),
            explanation=f"Supplier filed tax ₹{new_tax:,} diverging from calculated ₹{orig_tax:,} (discrepancy of ₹{diff:,})."
        )
        self.anomaly_log.append(record)
        return invoice

    def inject_hsn_mismatch(self, invoice: Invoice) -> Invoice:
        """Injects mismatched HSN code between supplier GSTR-1 and buyer register."""
        orig_hsn = invoice.hsn_code
        wrong_hsn = "9999" if orig_hsn != "9999" else "8471"
        invoice.hsn_code = wrong_hsn
        invoice.anomaly_type = AnomalyType.HSN_MISMATCH.value
        invoice.anomaly_severity = AnomalySeverity.LOW.value

        record = InjectedAnomalyRecord(
            anomaly_type=AnomalyType.HSN_MISMATCH,
            severity=AnomalySeverity.LOW,
            invoice_id=invoice.invoice_id,
            vendor_id=invoice.vendor_id,
            tax_period=invoice.tax_period,
            affected_fields=["hsn_code"],
            original_value=orig_hsn,
            anomalous_value=wrong_hsn,
            explanation=f"HSN code reported as {wrong_hsn} instead of legitimate classification {orig_hsn}."
        )
        self.anomaly_log.append(record)
        return invoice

    def inject_date_mismatch(self, invoice: Invoice) -> Invoice:
        """Shifts invoice date across calendar month boundaries."""
        orig_date = invoice.invoice_date
        shift_days = self.rng.choice([15, 25, 35])
        new_date = orig_date - timedelta(days=shift_days)
        invoice.invoice_date = new_date
        invoice.anomaly_type = AnomalyType.DATE_MISMATCH.value
        invoice.anomaly_severity = AnomalySeverity.MEDIUM.value

        record = InjectedAnomalyRecord(
            anomaly_type=AnomalyType.DATE_MISMATCH,
            severity=AnomalySeverity.MEDIUM,
            invoice_id=invoice.invoice_id,
            vendor_id=invoice.vendor_id,
            tax_period=invoice.tax_period,
            affected_fields=["invoice_date"],
            original_value=str(orig_date),
            anomalous_value=str(new_date),
            explanation=f"Invoice date {new_date} misaligned across return period boundary compared to reported {orig_date}."
        )
        self.anomaly_log.append(record)
        return invoice

    def create_duplicate_invoice(self, base_invoice: Invoice, near_duplicate: bool = False) -> Invoice:
        """
        Clones an invoice as an exact duplicate or near-duplicate variation.
        Near-duplicates test fuzzy matching and entity resolution.
        """
        dup_id = f"{base_invoice.invoice_id}-DUP"
        inv_dict = base_invoice.model_dump()
        inv_dict["invoice_id"] = dup_id
        inv_dict["is_duplicate"] = True

        if near_duplicate:
            # Variant: suffix variation, date shift +- 1 day, or tiny paise shift
            variation_type = self.rng.choice(["number_suffix", "date_shift", "paise_rounding"])
            if variation_type == "number_suffix":
                inv_dict["invoice_number"] = f"{base_invoice.invoice_number}/A"
                exp = f"Near-duplicate with invoice number variation '{inv_dict['invoice_number']}'"
            elif variation_type == "date_shift":
                inv_dict["invoice_date"] = base_invoice.invoice_date + timedelta(days=1)
                exp = f"Near-duplicate with 1-day shifted date '{inv_dict['invoice_date']}'"
            else:
                inv_dict["taxable_value"] = base_invoice.taxable_value + Decimal("0.50")
                inv_dict["invoice_value"] = base_invoice.invoice_value + Decimal("0.50")
                exp = "Near-duplicate with 50 paise rounding discrepancy"
            
            inv_dict["anomaly_type"] = AnomalyType.NEAR_DUPLICATE_INVOICE.value
            inv_dict["anomaly_severity"] = AnomalySeverity.HIGH.value
            anom_type = AnomalyType.NEAR_DUPLICATE_INVOICE
        else:
            inv_dict["anomaly_type"] = AnomalyType.DUPLICATE_INVOICE.value
            inv_dict["anomaly_severity"] = AnomalySeverity.CRITICAL.value
            anom_type = AnomalyType.DUPLICATE_INVOICE
            exp = f"Exact duplicate invoice submitted for double ITC credit: {base_invoice.invoice_number}"

        dup_invoice = Invoice(**inv_dict)
        self.anomaly_log.append(InjectedAnomalyRecord(
            anomaly_type=anom_type,
            severity=dup_invoice.anomaly_severity,
            invoice_id=dup_id,
            vendor_id=dup_invoice.vendor_id,
            tax_period=dup_invoice.tax_period,
            affected_fields=["invoice_number", "is_duplicate"],
            original_value=base_invoice.invoice_number,
            anomalous_value=dup_invoice.invoice_number,
            explanation=exp
        ))
        return dup_invoice

    def inject_taxable_value_mismatch(self, invoice: Invoice, discrepancy_amt: Decimal = Decimal("5000.00")) -> Invoice:
        """Modifies declared taxable value between returns (e.g. buyer books 100k, supplier filed 95k)."""
        orig_val = invoice.taxable_value
        new_val = max(Decimal("100.00"), (orig_val - discrepancy_amt).quantize(TWOPLACES))
        invoice.taxable_value = new_val
        invoice.invoice_value = (invoice.taxable_value + invoice.total_tax).quantize(TWOPLACES)
        invoice.anomaly_type = AnomalyType.TAXABLE_VALUE_MISMATCH.value
        invoice.anomaly_severity = AnomalySeverity.MEDIUM.value

        self.anomaly_log.append(InjectedAnomalyRecord(
            anomaly_type=AnomalyType.TAXABLE_VALUE_MISMATCH,
            severity=AnomalySeverity.MEDIUM,
            invoice_id=invoice.invoice_id,
            vendor_id=invoice.vendor_id,
            tax_period=invoice.tax_period,
            affected_fields=["taxable_value", "invoice_value"],
            original_value=str(orig_val),
            anomalous_value=str(new_val),
            explanation=f"Supplier taxable value ₹{new_val:,} diverges from buyer purchase register ₹{orig_val:,}."
        ))
        return invoice

    def inject_unusual_transaction(self, invoice: Invoice, spike_multiplier: float = 12.0) -> Invoice:
        """Injects anomalous velocity or value spike uncharacteristic of vendor's historical volume."""
        orig_val = invoice.taxable_value
        new_val = (orig_val * Decimal(str(spike_multiplier))).quantize(TWOPLACES)
        invoice.taxable_value = new_val
        # Recalculate tax
        if invoice.supply_type == SupplyType.INTRA_STATE:
            half = (invoice.total_tax * Decimal(str(spike_multiplier)) / Decimal("2.00")).quantize(TWOPLACES)
            invoice.cgst = half
            invoice.sgst = half
            invoice.igst = Decimal("0.00")
        else:
            invoice.cgst = Decimal("0.00")
            invoice.sgst = Decimal("0.00")
            invoice.igst = (invoice.total_tax * Decimal(str(spike_multiplier))).quantize(TWOPLACES)
        invoice.total_tax = (invoice.cgst + invoice.sgst + invoice.igst).quantize(TWOPLACES)
        invoice.invoice_value = (invoice.taxable_value + invoice.total_tax).quantize(TWOPLACES)
        invoice.anomaly_type = AnomalyType.UNUSUAL_TRANSACTION.value
        invoice.anomaly_severity = AnomalySeverity.HIGH.value

        self.anomaly_log.append(InjectedAnomalyRecord(
            anomaly_type=AnomalyType.UNUSUAL_TRANSACTION,
            severity=AnomalySeverity.HIGH,
            invoice_id=invoice.invoice_id,
            vendor_id=invoice.vendor_id,
            tax_period=invoice.tax_period,
            affected_fields=["taxable_value", "total_tax", "invoice_value"],
            original_value=str(orig_val),
            anomalous_value=str(new_val),
            explanation=f"Unusual {spike_multiplier:.1f}x transaction value surge (₹{orig_val:,} -> ₹{new_val:,})."
        ))
        return invoice

    def log_custom_anomaly(
        self,
        anomaly_type: AnomalyType,
        severity: AnomalySeverity,
        invoice_id: str,
        vendor_id: str,
        tax_period: str,
        affected_fields: List[str],
        explanation: str
    ):
        """Log compliance, filing, or graph-level anomaly event."""
        self.anomaly_log.append(InjectedAnomalyRecord(
            anomaly_type=anomaly_type,
            severity=severity,
            invoice_id=invoice_id,
            vendor_id=vendor_id,
            tax_period=tax_period,
            affected_fields=affected_fields,
            original_value=None,
            anomalous_value=None,
            explanation=explanation
        ))
