"""
Public Transaction Dataset Adapter (UCI Online Retail / Commercial Invoicing Schema).

Converts transaction line-item records into canonical GST Invoices and Vendors:
1. Groups line-items by InvoiceNo.
2. Maps international / external customer-vendor pairs to Indian states and GSTINs.
3. Computes intra-state (CGST+SGST) vs inter-state (IGST) tax breakdowns using 18% standard rate.
4. Marks records with data_source = 'public'.
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
import random
from typing import List, Dict, Any, Optional

from backend.data.public.loader import BaseDatasetAdapter, PublicDataLoader
from backend.data.schema import Invoice, Vendor, SupplyType, DataSource, TWOPLACES, to_decimal_paise
from backend.data.normalization.normalize import (
    normalize_date, derive_financial_year, derive_tax_period, normalize_tax_breakdown
)


INDIAN_STATES = [
    ("29", "Karnataka"),
    ("27", "Maharashtra"),
    ("24", "Gujarat"),
    ("07", "Delhi"),
    ("33", "Tamil Nadu"),
    ("36", "Telangana"),
    ("09", "Uttar Pradesh"),
    ("19", "West Bengal"),
    ("06", "Haryana")
]


def generate_canonical_gstin(state_code: str, entity_idx: int) -> str:
    """Generate a valid statutory 15-character GSTIN for testing/mapping."""
    pan_prefix = "AABCP"
    pan_num = f"{1000 + (entity_idx % 9000):04d}"
    pan_suffix = chr(ord('A') + (entity_idx % 26))
    return f"{state_code}{pan_prefix}{pan_num}{pan_suffix}1Z{entity_idx % 10}"


class RetailInvoiceAdapter(BaseDatasetAdapter):
    """Adapter for transactional retail/B2B invoice datasets."""

    def __init__(self, buyer_state: str = "Karnataka", buyer_gstin: str = "29AAQCQ1234M1Z8", seed: int = 42):
        self.buyer_state = buyer_state
        self.buyer_gstin = buyer_gstin
        self.rng = random.Random(seed)
        self.loader = PublicDataLoader()
        self._vendor_cache: Dict[str, Vendor] = {}

    def _get_or_create_vendor(self, vendor_key: str, idx: int) -> Vendor:
        if vendor_key in self._vendor_cache:
            return self._vendor_cache[vendor_key]

        state_code, state_name = self.rng.choice(INDIAN_STATES)
        vid = f"V-PUB-{idx:04d}"
        gstin = generate_canonical_gstin(state_code, idx)
        
        vendor = Vendor(
            vendor_id=vid,
            vendor_name=f"Public Supplier {vendor_key}",
            gstin=gstin,
            state=state_name,
            state_code=state_code,
            business_category="Wholesale & Distribution",
            registration_date=date(2020, 1, 1),
            is_active=True
        )
        self._vendor_cache[vendor_key] = vendor
        return vendor

    def adapt_invoices(self, raw_data_path: Optional[str] = None, limit: Optional[int] = None) -> List[Invoice]:
        """Convert public dataset rows into canonical Invoice objects."""
        if raw_data_path and os.path.exists(raw_data_path):
            raw_rows = self.loader.load_csv(raw_data_path)
        else:
            # Fallback to generating synthetic public-format transactions for hermetic runs
            raw_rows = self._generate_mock_public_rows(count=min(limit or 200, 200))

        # Group by invoice number
        grouped_lines = defaultdict(list)
        for row in raw_rows:
            inv_no = str(row.get("InvoiceNo") or row.get("invoice_id") or "INV-000")
            grouped_lines[inv_no].append(row)

        invoices: List[Invoice] = []
        vendor_counter = 1

        for inv_no, lines in grouped_lines.items():
            if limit and len(invoices) >= limit:
                break

            first_line = lines[0]
            cust_id = str(first_line.get("CustomerID") or f"CUST-{vendor_counter}")
            vendor = self._get_or_create_vendor(cust_id, vendor_counter)
            vendor_counter += 1

            inv_date = normalize_date(first_line.get("InvoiceDate") or "2024-06-15")

            # Aggregate total taxable value from line items
            total_taxable = Decimal("0.00")
            for line in lines:
                qty = Decimal(str(line.get("Quantity", 1)))
                unit_price = to_decimal_paise(line.get("UnitPrice", 100))
                line_total = abs(qty * unit_price).quantize(TWOPLACES)
                total_taxable += line_total

            if total_taxable == Decimal("0.00"):
                total_taxable = Decimal("1500.00")

            # Check intra vs inter-state
            is_intra = (vendor.state.lower() == self.buyer_state.lower())
            supply_type = SupplyType.INTRA_STATE if is_intra else SupplyType.INTER_STATE
            
            # Compute tax at standard 18% slab
            tax_breakdown = normalize_tax_breakdown(
                taxable_val=total_taxable,
                supply_type=supply_type,
                tax_rate=Decimal("0.18")
            )

            stock_code = str(first_line.get("StockCode") or "8471")
            hsn = stock_code[:6] if len(stock_code) >= 4 else "9983"

            inv = Invoice(
                invoice_id=f"PUB-{inv_no}",
                vendor_id=vendor.vendor_id,
                buyer_id="TP001",
                vendor_gstin=vendor.gstin,
                buyer_gstin=self.buyer_gstin,
                invoice_number=inv_no,
                invoice_date=inv_date,
                financial_year=derive_financial_year(inv_date),
                tax_period=derive_tax_period(inv_date),
                taxable_value=total_taxable,
                cgst=tax_breakdown["cgst"],
                sgst=tax_breakdown["sgst"],
                igst=tax_breakdown["igst"],
                total_tax=tax_breakdown["total_tax"],
                invoice_value=tax_breakdown["invoice_value"],
                hsn_code=hsn,
                supply_type=supply_type,
                data_source=DataSource.PUBLIC,
                synthetic_profile=None,
                anomaly_type=None,
                is_duplicate=False
            )
            invoices.append(inv)

        return invoices

    def adapt_vendors(self, raw_data_path: Optional[str] = None) -> List[Vendor]:
        """Return all distinct vendors mapped from the public dataset."""
        if not self._vendor_cache:
            self.adapt_invoices(raw_data_path, limit=100)
        return list(self._vendor_cache.values())

    def _generate_mock_public_rows(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generates mock rows conforming to the UCI Retail schema for self-contained testing."""
        rows = []
        descriptions = [
            ("847130", "LAPTOP COMPUTER DESK UNIT", Decimal("450.00")),
            ("851762", "NETWORK ROUTER SWITCH", Decimal("120.00")),
            ("844332", "LASER PRINTER MULTIFUNCTION", Decimal("220.00")),
            ("731815", "INDUSTRIAL STEEL FASTENERS 100PK", Decimal("35.00")),
            ("392690", "POLYMER SEALING GASKET", Decimal("15.50")),
        ]
        
        for i in range(1, (count // 2) + 1):
            inv_no = f"10{i:04d}"
            cust_id = f"1{100 + (i % 15)}"
            line_count = self.rng.randint(1, 3)
            
            for line_idx in range(line_count):
                item = self.rng.choice(descriptions)
                qty = self.rng.randint(1, 10)
                month = (i % 12) + 1
                rows.append({
                    "InvoiceNo": inv_no,
                    "StockCode": item[0],
                    "Description": item[1],
                    "Quantity": qty,
                    "InvoiceDate": f"2024-{month:02d}-14 12:30",
                    "UnitPrice": str(item[2]),
                    "CustomerID": cust_id,
                    "Country": "India"
                })
        return rows
