"""
Synthetic Invoice Generator.

Creates realistic, internally consistent GST invoices adhering strictly to:
- State jurisdiction tax routing (Intra-state CGST+SGST vs Inter-state IGST)
- Standard GST rate slabs (5%, 12%, 18%, 28%)
- HSN / SAC categorization
- Decimal paise precision
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import random
from typing import List, Dict, Optional, Tuple

from backend.data.schema import Invoice, Vendor, SupplyType, DataSource, TWOPLACES
from backend.data.synthetic.profiles import PROFILES, VendorBehaviorProfile
from backend.data.normalization.normalize import derive_financial_year, derive_tax_period


# Standard B2B HSN codes with typical GST tax rate
HSN_CATALOG = [
    ("7208", "Hot-rolled products of iron or non-alloy steel", Decimal("0.18")),
    ("7210", "Flat-rolled products of iron clad or coated", Decimal("0.18")),
    ("8471", "Automatic data processing machines & computers", Decimal("0.18")),
    ("8517", "Telephone sets, routers, transmission apparatus", Decimal("0.18")),
    ("3004", "Medicaments consisting of mixed or unmixed products", Decimal("0.12")),
    ("2710", "Petroleum oils and oils from bituminous minerals", Decimal("0.18")),
    ("8708", "Parts and accessories of motor vehicles", Decimal("0.28")),
    ("9983", "Other professional, technical and business services", Decimal("0.18")),
    ("9972", "Real estate services on a fee or commission basis", Decimal("0.18")),
    ("4819", "Cartons, boxes, cases of corrugated paper", Decimal("0.12")),
    ("3923", "Articles for the conveyance or packing of plastics", Decimal("0.18")),
    ("1701", "Cane or beet sugar and chemically pure sucrose", Decimal("0.05")),
]


class InvoiceGenerator:
    """Generates synthetic invoices with authentic B2B ticket distributions."""

    def __init__(self, buyer_state: str = "Karnataka", buyer_gstin: str = "29AAQCQ1234M1Z8", seed: int = 42):
        self.buyer_state = buyer_state
        self.buyer_gstin = buyer_gstin
        self.rng = random.Random(seed)

    def generate_invoice_for_vendor(
        self,
        vendor: Vendor,
        inv_index: int,
        invoice_date: date,
        profile: Optional[VendorBehaviorProfile] = None
    ) -> Invoice:
        """Constructs an individual pristine invoice before any anomaly injection."""
        prof = profile or PROFILES.get(getattr(vendor, "synthetic_profile", "A"), PROFILES["A"])
        
        # Determine base ticket value based on profile multiplier
        base_mean = 125000.0 * prof.average_ticket_multiplier
        # Log-normal distribution of ticket sizes
        raw_val = self.rng.lognormvariate(mu=11.2, sigma=0.8) * prof.average_ticket_multiplier
        taxable_value = Decimal(str(max(5000.0, round(raw_val, 2)))).quantize(TWOPLACES)

        # Select HSN item and GST slab
        hsn_item = self.rng.choice(HSN_CATALOG)
        hsn_code = hsn_item[0]
        tax_rate = hsn_item[2]

        total_tax = (taxable_value * tax_rate).quantize(TWOPLACES, rounding=ROUND_HALF_UP)

        # Supply type routing
        is_intra = (vendor.state.strip().lower() == self.buyer_state.strip().lower())
        if is_intra:
            supply_type = SupplyType.INTRA_STATE
            cgst = (total_tax / Decimal("2.00")).quantize(TWOPLACES, rounding=ROUND_HALF_UP)
            sgst = total_tax - cgst
            igst = Decimal("0.00")
        else:
            supply_type = SupplyType.INTER_STATE
            cgst = Decimal("0.00")
            sgst = Decimal("0.00")
            igst = total_tax

        invoice_value = (taxable_value + total_tax).quantize(TWOPLACES)
        inv_no = f"INV-{invoice_date.year}-{inv_index:04d}"
        inv_id = f"{vendor.vendor_id}-{inv_no}"

        return Invoice(
            invoice_id=inv_id,
            vendor_id=vendor.vendor_id,
            buyer_id="TP001",
            vendor_gstin=vendor.gstin,
            buyer_gstin=self.buyer_gstin,
            invoice_number=inv_no,
            invoice_date=invoice_date,
            financial_year=derive_financial_year(invoice_date),
            tax_period=derive_tax_period(invoice_date),
            taxable_value=taxable_value,
            cgst=cgst,
            sgst=sgst,
            igst=igst,
            total_tax=total_tax,
            invoice_value=invoice_value,
            hsn_code=hsn_code,
            supply_type=supply_type,
            data_source=DataSource.SYNTHETIC,
            synthetic_profile=prof.code,
            anomaly_type=None,
            is_duplicate=False
        )
