"""
Behavioral Profiles for GST Taxpayer Simulation.

Defines distinct compliance personalities (Profiles A through H)
that govern filing discipline, invoice accuracy, reporting consistency,
and network topology.

IMPORTANT NOTE:
The class distributions and profile transition probabilities defined herein
are experimental sampling configurations designed for machine learning model
training and balance. They do NOT represent the actual statutory prevalence
or real-world distribution of GST non-compliance in India.
"""

from dataclasses import dataclass
import random
from typing import Dict, Any, List, Tuple


@dataclass
class VendorBehaviorProfile:
    code: str
    name: str
    description: str
    mismatch_probability: float
    tax_error_probability: float
    filing_delay_mean: float
    filing_delay_std: float
    missing_gstr1_probability: float
    missing_gstr3b_probability: float
    missing_einvoice_probability: float
    missing_ewaybill_probability: float
    duplicate_probability: float
    is_network_suspicious: bool = False
    average_ticket_multiplier: float = 1.0


PROFILES: Dict[str, VendorBehaviorProfile] = {
    "A": VendorBehaviorProfile(
        code="A",
        name="Compliant Vendor",
        description="Low mismatch rate, on-time filing, valid invoices, high e-invoice & e-way bill compliance.",
        mismatch_probability=0.01,
        tax_error_probability=0.005,
        filing_delay_mean=0.0,
        filing_delay_std=0.5,
        missing_gstr1_probability=0.0,
        missing_gstr3b_probability=0.0,
        missing_einvoice_probability=0.0,
        missing_ewaybill_probability=0.01,
        duplicate_probability=0.0,
        average_ticket_multiplier=1.0,
    ),
    "B": VendorBehaviorProfile(
        code="B",
        name="Occasional Mismatch",
        description="Low-to-medium mismatch rate, occasional minor tax calculation discrepancies or 1-3 day delays.",
        mismatch_probability=0.15,
        tax_error_probability=0.12,
        filing_delay_mean=4.0,
        filing_delay_std=2.5,
        missing_gstr1_probability=0.02,
        missing_gstr3b_probability=0.02,
        missing_einvoice_probability=0.08,
        missing_ewaybill_probability=0.08,
        duplicate_probability=0.02,
        average_ticket_multiplier=1.0,
    ),
    "C": VendorBehaviorProfile(
        code="C",
        name="Chronic Mismatch",
        description="High mismatch rate, repeated invoice discrepancies (tax amount/taxable value), chronic delays.",
        mismatch_probability=0.45,
        tax_error_probability=0.35,
        filing_delay_mean=18.0,
        filing_delay_std=6.0,
        missing_gstr1_probability=0.35,
        missing_gstr3b_probability=0.30,
        missing_einvoice_probability=0.35,
        missing_ewaybill_probability=0.30,
        duplicate_probability=0.08,
        average_ticket_multiplier=1.1,
    ),
    "D": VendorBehaviorProfile(
        code="D",
        name="Late Filer",
        description="Mostly valid invoices and arithmetic, but frequent significant filing delays (15-45 days).",
        mismatch_probability=0.08,
        tax_error_probability=0.04,
        filing_delay_mean=25.0,
        filing_delay_std=7.0,
        missing_gstr1_probability=0.03,
        missing_gstr3b_probability=0.06,
        missing_einvoice_probability=0.10,
        missing_ewaybill_probability=0.08,
        duplicate_probability=0.01,
        average_ticket_multiplier=1.0,
    ),
    "E": VendorBehaviorProfile(
        code="E",
        name="Missing-Return Vendor",
        description="Invoices reported by buyer in Purchase Register, but supplier repeatedly fails to file GSTR-1 or GSTR-3B.",
        mismatch_probability=0.55,
        tax_error_probability=0.20,
        filing_delay_mean=32.0,
        filing_delay_std=8.0,
        missing_gstr1_probability=0.65,
        missing_gstr3b_probability=0.75,
        missing_einvoice_probability=0.45,
        missing_ewaybill_probability=0.40,
        duplicate_probability=0.04,
        average_ticket_multiplier=1.2,
    ),
    "F": VendorBehaviorProfile(
        code="F",
        name="High ITC Exposure",
        description="Substantial transaction amounts (5x-20x average); mostly compliant but represents high systemic risk.",
        mismatch_probability=0.08,
        tax_error_probability=0.04,
        filing_delay_mean=3.0,
        filing_delay_std=2.0,
        missing_gstr1_probability=0.02,
        missing_gstr3b_probability=0.02,
        missing_einvoice_probability=0.02,
        missing_ewaybill_probability=0.03,
        duplicate_probability=0.0,
        average_ticket_multiplier=10.0,
    ),
    "G": VendorBehaviorProfile(
        code="G",
        name="Suspicious Network",
        description="Unusually dense circular trading relationships with a small syndicate of entities, anomalous invoice velocity.",
        mismatch_probability=0.35,
        tax_error_probability=0.25,
        filing_delay_mean=12.0,
        filing_delay_std=6.0,
        missing_gstr1_probability=0.40,
        missing_gstr3b_probability=0.45,
        missing_einvoice_probability=0.45,
        missing_ewaybill_probability=0.45,
        duplicate_probability=0.15,
        is_network_suspicious=True,
        average_ticket_multiplier=3.5,
    ),
    "H": VendorBehaviorProfile(
        code="H",
        name="Duplicate / Near-Duplicate Generator",
        description="Generates exact duplicates, invoice number suffix variations, date shifts (+-1 day), and penny rounding variants.",
        mismatch_probability=0.55,
        tax_error_probability=0.20,
        filing_delay_mean=6.0,
        filing_delay_std=4.0,
        missing_gstr1_probability=0.15,
        missing_gstr3b_probability=0.15,
        missing_einvoice_probability=0.20,
        missing_ewaybill_probability=0.20,
        duplicate_probability=0.70,
        average_ticket_multiplier=1.0,
    )
}

# Balanced experimental distribution to achieve target:
# Low: 60–70%, Medium: 20–25%, High: 10–15%
BALANCED_PROFILE_DISTRIBUTION: List[Tuple[str, float]] = [
    ("A", 0.54),  # Compliant -> Low
    ("B", 0.16),  # Occasional Mismatch -> Med
    ("C", 0.08),  # Chronic Mismatch -> High
    ("D", 0.10),  # Late Filer -> Med
    ("E", 0.05),  # Missing Return -> High
    ("F", 0.03),  # High ITC Exposure -> Low/Med
    ("G", 0.02),  # Suspicious Network -> High/Med
    ("H", 0.02),  # Duplicate Generator -> High/Med
]

# Baseline Phase 1 distribution (preserved for backward compatibility)
PHASE1_PROFILE_DISTRIBUTION: List[Tuple[str, float]] = [
    ("A", 0.58),
    ("B", 0.14),
    ("C", 0.06),
    ("D", 0.08),
    ("E", 0.04),
    ("F", 0.04),
    ("G", 0.03),
    ("H", 0.03),
]

# Controlled Markov Profile Transitions (quarterly / drift probability)
# Maps current profile -> list of (next_profile, transition_probability)
PROFILE_TRANSITIONS: Dict[str, List[Tuple[str, float]]] = {
    "A": [("A", 0.94), ("B", 0.04), ("D", 0.02)],
    "B": [("B", 0.90), ("A", 0.05), ("C", 0.03), ("D", 0.02)],
    "C": [("C", 0.88), ("B", 0.07), ("E", 0.04), ("A", 0.01)],
    "D": [("D", 0.90), ("A", 0.05), ("B", 0.03), ("E", 0.02)],
    "E": [("E", 0.88), ("C", 0.07), ("D", 0.03), ("B", 0.02)],
    "F": [("F", 0.94), ("A", 0.04), ("B", 0.02)],
    "G": [("G", 0.92), ("C", 0.05), ("A", 0.03)],
    "H": [("H", 0.92), ("B", 0.05), ("C", 0.03)],
}


def sample_profile_transition(current_profile: str, rng: random.Random) -> str:
    """Sample next profile given current profile under Markov behavioral drift."""
    transitions = PROFILE_TRANSITIONS.get(current_profile, [("A", 1.0)])
    next_profiles, weights = zip(*transitions)
    return rng.choices(next_profiles, weights=weights, k=1)[0]
