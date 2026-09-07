"""
Canonical GST Transaction & Compliance Schema.

All financial amounts are represented using Python `Decimal` (quantized to 2 decimal
places / paise) to prevent floating-point representation drift and rounding errors.
"""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator


TWOPLACES = Decimal("0.01")


def to_decimal_paise(val: Any) -> Decimal:
    """Helper to safely convert any numeric or string amount to Decimal with 2 places."""
    if val is None:
        return Decimal("0.00")
    if isinstance(val, Decimal):
        return val.quantize(TWOPLACES, rounding=ROUND_HALF_UP)
    # Strip any formatting symbols like commas or currency symbols
    clean_str = str(val).replace(",", "").replace("₹", "").strip()
    if not clean_str:
        return Decimal("0.00")
    return Decimal(clean_str).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


class SupplyType(str, Enum):
    INTRA_STATE = "INTRA_STATE"   # CGST + SGST
    INTER_STATE = "INTER_STATE"   # IGST


class DataSource(str, Enum):
    PUBLIC = "public"
    SYNTHETIC = "synthetic"
    DERIVED = "derived"


class ReconciliationStatus(str, Enum):
    MATCHED = "Matched"
    TAX_MISMATCH = "Tax Amount Mismatch"
    TAXABLE_VALUE_MISMATCH = "Taxable Value Mismatch"
    MISSING_IN_GSTR1 = "Missing in GSTR-1"
    MISSING_IN_GSTR2B = "Missing in GSTR-2B"
    MISSING_IN_PR = "Missing in Purchase Register"
    HSN_MISMATCH = "HSN Mismatch"
    DATE_MISMATCH = "Date Mismatch"
    DUPLICATE_INVOICE = "Duplicate Invoice"
    LATE_FILING = "Late Filing"
    UNPAID_TAX_CHAIN = "Unpaid Tax Chain (GSTR-3B Missing)"


class RiskLabel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


# -------------------------------------------------------------------
# 1. Vendor Model
# -------------------------------------------------------------------
class Vendor(BaseModel):
    vendor_id: str = Field(..., description="Unique internal vendor ID, e.g. V001")
    vendor_name: str = Field(..., description="Legal or trade name of vendor")
    gstin: str = Field(..., min_length=15, max_length=15, description="15-character GSTIN")
    state: str = Field(..., description="State name, e.g. Karnataka")
    state_code: Optional[str] = Field(None, description="2-digit state code, e.g. '29'")
    business_category: str = Field("Manufacturing", description="Industry or business sector")
    registration_date: Optional[date] = Field(None, description="Date of GST registration")
    is_active: bool = Field(True, description="Whether the vendor is actively registered")
    synthetic_profile: Optional[str] = Field(None, description="Behavioral profile A-H if synthetic")

    @field_validator("gstin")
    @classmethod
    def validate_gstin_format(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 15:
            raise ValueError(f"GSTIN must be exactly 15 characters, got {len(v)}")
        if not v[:2].isdigit():
            raise ValueError(f"GSTIN must start with 2-digit state code, got '{v[:2]}'")
        return v

    @model_validator(mode="after")
    def populate_state_code(self):
        if not self.state_code and self.gstin:
            self.state_code = self.gstin[:2]
        return self


# -------------------------------------------------------------------
# 2. Invoice Model
# -------------------------------------------------------------------
class Invoice(BaseModel):
    invoice_id: str = Field(..., description="Unique system-wide invoice identifier")
    vendor_id: str = Field(..., description="Issuing vendor ID")
    buyer_id: str = Field("TP001", description="Customer / Taxpayer ID claiming ITC")
    vendor_gstin: Optional[str] = Field(None, description="Supplier GSTIN")
    buyer_gstin: Optional[str] = Field(None, description="Buyer GSTIN")
    invoice_number: str = Field(..., description="Supplier's invoice number, e.g. INV-2024-001")
    invoice_date: date = Field(..., description="Date of invoice issuance")
    financial_year: str = Field(..., description="Financial year, e.g. '2024-25'")
    tax_period: str = Field(..., description="Filing period YYYY-MM, e.g. '2024-07'")
    
    # Financial fields with Decimal paise
    taxable_value: Decimal = Field(..., description="Base value of goods/services")
    cgst: Decimal = Field(Decimal("0.00"), description="Central GST")
    sgst: Decimal = Field(Decimal("0.00"), description="State GST")
    igst: Decimal = Field(Decimal("0.00"), description="Integrated GST")
    total_tax: Decimal = Field(..., description="Sum of CGST + SGST + IGST")
    invoice_value: Decimal = Field(..., description="Total invoice amount (taxable + tax)")
    
    hsn_code: str = Field("9983", description="HSN/SAC code (4 to 8 digits)")
    supply_type: SupplyType = Field(SupplyType.INTRA_STATE, description="INTRA_STATE or INTER_STATE")
    
    # Provenance and metadata
    data_source: DataSource = Field(DataSource.SYNTHETIC, description="Origin of record")
    synthetic_profile: Optional[str] = Field(None, description="Behavioral profile A-H if synthetic")
    anomaly_type: Optional[str] = Field(None, description="Injected anomaly type if any")
    anomaly_severity: Optional[str] = Field(None, description="Severity: LOW, MEDIUM, HIGH, CRITICAL")
    is_duplicate: bool = Field(False, description="Flag indicating duplicate/near-duplicate invoice")

    @field_validator("taxable_value", "cgst", "sgst", "igst", "total_tax", "invoice_value", mode="before")
    @classmethod
    def parse_money(cls, v: Any) -> Decimal:
        return to_decimal_paise(v)

    @model_validator(mode="after")
    def validate_supply_type_and_totals(self):
        # Ensure non-negative amounts
        for field_name in ["taxable_value", "cgst", "sgst", "igst", "total_tax", "invoice_value"]:
            val = getattr(self, field_name)
            if val < Decimal("0.00"):
                raise ValueError(f"{field_name} cannot be negative: {val}")
        
        # Validate arithmetic consistency (allowing a small rounding tolerance of 0.05 for external data)
        computed_tax = (self.cgst + self.sgst + self.igst).quantize(TWOPLACES)
        if abs(self.total_tax - computed_tax) > Decimal("0.05"):
            # If total_tax was not set properly, reconcile it
            self.total_tax = computed_tax
            
        computed_inv_val = (self.taxable_value + self.total_tax).quantize(TWOPLACES)
        if abs(self.invoice_value - computed_inv_val) > Decimal("0.05"):
            self.invoice_value = computed_inv_val

        return self


# -------------------------------------------------------------------
# 3. Filing Model
# -------------------------------------------------------------------
class Filing(BaseModel):
    vendor_id: str = Field(..., description="Vendor ID")
    tax_period: str = Field(..., description="Filing period YYYY-MM")
    gstr1_filed: bool = Field(True, description="Whether GSTR-1 was filed")
    gstr1_filing_date: Optional[date] = Field(None, description="Actual GSTR-1 filing date")
    gstr3b_filed: bool = Field(True, description="Whether GSTR-3B was filed (tax remitted)")
    gstr3b_filing_date: Optional[date] = Field(None, description="Actual GSTR-3B filing date")
    filing_delay_days: int = Field(0, ge=0, description="Delay in days past the 20th statutory deadline")
    data_source: DataSource = Field(DataSource.SYNTHETIC)


# -------------------------------------------------------------------
# 4. Reconciliation Model
# -------------------------------------------------------------------
class Reconciliation(BaseModel):
    invoice_id: str = Field(..., description="Invoice ID")
    vendor_id: str = Field(..., description="Issuing vendor ID")
    tax_period: str = Field(..., description="Tax period YYYY-MM")
    gstr1_present: bool = Field(True, description="Present in supplier GSTR-1")
    gstr2b_present: bool = Field(True, description="Present in buyer GSTR-2B")
    purchase_register_present: bool = Field(True, description="Present in buyer Purchase Register")
    tax_amount_match: bool = Field(True, description="Tax amount matches between returns")
    taxable_value_match: bool = Field(True, description="Taxable value matches between returns")
    hsn_match: bool = Field(True, description="HSN matches")
    date_match: bool = Field(True, description="Invoice date matches")
    einvoice_present: bool = Field(True, description="Has valid e-Invoice IRN")
    ewaybill_present: bool = Field(True, description="Has valid e-Way Bill")
    reconciliation_status: ReconciliationStatus = Field(
        ReconciliationStatus.MATCHED, description="Final status classification"
    )
    discrepancy_amount: Decimal = Field(Decimal("0.00"), description="Discrepancy or tax at risk")

    @field_validator("discrepancy_amount", mode="before")
    @classmethod
    def parse_discrepancy(cls, v: Any) -> Decimal:
        return to_decimal_paise(v)


# -------------------------------------------------------------------
# 5. ITC / Risk Summary Model
# -------------------------------------------------------------------
class ITCRiskSummary(BaseModel):
    vendor_id: str = Field(..., description="Vendor ID")
    tax_period: str = Field(..., description="Tax period YYYY-MM")
    itc_exposure: Decimal = Field(Decimal("0.00"), description="Total ITC claimed from this vendor in period")
    mismatch_count: int = Field(0, ge=0, description="Count of mismatched invoices in period")
    mismatch_rate: float = Field(0.0, ge=0.0, le=1.0, description="Proportion of invoices with mismatches")
    missing_return_count: int = Field(0, ge=0, description="Count of unfiled GSTR-1 or GSTR-3B returns")
    compliance_score: Decimal = Field(Decimal("1.00"), description="Calculated compliance score 0.00 to 1.00")
    risk_label: RiskLabel = Field(RiskLabel.LOW, description="Low, Medium, or High Risk")

    @field_validator("itc_exposure", "compliance_score", mode="before")
    @classmethod
    def parse_summary_decimals(cls, v: Any) -> Decimal:
        return to_decimal_paise(v)


# -------------------------------------------------------------------
# 6. Vendor-Period Feature Vector (For ML without Data Leakage)
# -------------------------------------------------------------------
class VendorPeriodFeatures(BaseModel):
    """Features computed strictly on historical periods [t - lookback, t]."""
    vendor_id: str
    tax_period: str
    
    # Activity metrics
    invoice_count: int = 0
    total_invoice_value: Decimal = Decimal("0.00")
    average_invoice_value: Decimal = Decimal("0.00")
    total_tax: Decimal = Decimal("0.00")
    
    # Compliance & mismatch metrics
    mismatch_count: int = 0
    mismatch_rate: float = 0.0
    missing_gstr1_count: int = 0
    missing_gstr3b_count: int = 0
    late_filing_count: int = 0
    average_filing_delay: float = 0.0
    duplicate_invoice_count: int = 0
    missing_einvoice_count: int = 0
    missing_eway_bill_count: int = 0
    itc_exposure: Decimal = Decimal("0.00")
    
    # Network / Graph properties
    supplier_relationship_count: int = 1
    graph_degree: int = 1
    graph_centrality: float = 0.5
    
    # Historical risk state
    previous_period_risk: float = 0.0
    
    # Target period (future period t+1) ground-truth label - used ONLY for training evaluation
    target_period: Optional[str] = None
    target_compliance_score: Optional[float] = None
    target_risk_label: Optional[str] = None

    @field_validator("total_invoice_value", "average_invoice_value", "total_tax", "itc_exposure", mode="before")
    @classmethod
    def parse_features_decimals(cls, v: Any) -> Decimal:
        return to_decimal_paise(v)


# -------------------------------------------------------------------
# 7. Ground Truth Label Model
# -------------------------------------------------------------------
class GroundTruthLabel(BaseModel):
    vendor_id: str
    feature_period_end: str          # Last period included in features
    target_period: str              # Future period evaluated for outcome
    raw_risk_score: float           # 0.0 to 1.0
    risk_label: RiskLabel           # Low / Medium / High
    risk_factors: Dict[str, float]  # Component breakdown (delays, mismatches, unpaid tax)
    explanation: str
