"""
Synthetic Vendor Generation Module.

Generates realistic Indian business entities, statutory GSTINs,
geographical distribution across states, and assigns behavioral profiles.
"""

from datetime import date
import random
from typing import List, Dict, Optional, Tuple
from backend.data.schema import Vendor
from backend.data.synthetic.profiles import PROFILES, VendorBehaviorProfile


INDIAN_STATES_DATA = [
    ("29", "Karnataka", 0.18),
    ("27", "Maharashtra", 0.22),
    ("24", "Gujarat", 0.14),
    ("07", "Delhi", 0.10),
    ("33", "Tamil Nadu", 0.12),
    ("36", "Telangana", 0.08),
    ("09", "Uttar Pradesh", 0.06),
    ("19", "West Bengal", 0.05),
    ("06", "Haryana", 0.05),
]

BUSINESS_CATEGORIES = [
    "Industrial Machinery",
    "Steel & Metallurgy",
    "Chemicals & Petrochemicals",
    "Automotive Components",
    "Information Technology & Services",
    "Logistics & Warehousing",
    "Electrical Equipment",
    "Packaging Materials",
    "Textiles & Apparel",
    "Pharmaceuticals"
]

COMPANY_PREFIXES = [
    "Apex", "Bharat", "Zenith", "Prime", "Nexus", "Titan", "Vanguard", "Delta",
    "Paramount", "Horizon", "Sterling", "Kaveri", "Sahyadri", "Deccan", "Omega",
    "Precision", "United", "Global", "Imperial", "Galaxy"
]

COMPANY_SUFFIXES = [
    "Enterprises Pvt Ltd", "Industries Ltd", "Engineering Corp", "Solutions Pvt Ltd",
    "Technologies Ltd", "Logistics Pvt Ltd", "Manufacturing Co", "Trading Corp"
]

# Population distribution across profiles A-H
PROFILE_DISTRIBUTION = [
    ("A", 0.58),  # Compliant
    ("B", 0.14),  # Occasional Mismatch
    ("C", 0.06),  # Chronic Mismatch
    ("D", 0.08),  # Late Filer
    ("E", 0.04),  # Missing-Return Vendor
    ("F", 0.04),  # High ITC Exposure
    ("G", 0.03),  # Suspicious Network
    ("H", 0.03),  # Duplicate Generator
]


def make_gstin(state_code: str, entity_idx: int) -> str:
    """Construct a valid 15-character statutory GSTIN (2 state digits + 5 letters + 4 digits + 1 letter + 1 entity + Z + check)."""
    # First 3 letters: AAA to ZZZ
    # 4th letter: 'C' (Company) or 'P' (Person) or 'F' (Firm)
    # 5th letter: first letter of entity name (A-Z)
    l1 = chr(ord('A') + ((entity_idx // 676) % 26))
    l2 = chr(ord('A') + ((entity_idx // 26) % 26))
    l3 = chr(ord('A') + (entity_idx % 26))
    l4 = "C"
    l5 = chr(ord('A') + ((entity_idx * 7) % 26))
    pan_prefix = f"{l1}{l2}{l3}{l4}{l5}"
    
    pan_num = f"{1000 + (entity_idx % 9000):04d}"
    pan_suffix = chr(ord('A') + ((entity_idx * 3) % 26))
    pan = f"{pan_prefix}{pan_num}{pan_suffix}"
    entity_code = "1"
    check_char = "Z"
    check_digit = str((entity_idx * 3 + 7) % 10)
    return f"{state_code}{pan}{entity_code}{check_char}{check_digit}"


from backend.data.synthetic.profiles import (
    PROFILES, VendorBehaviorProfile, BALANCED_PROFILE_DISTRIBUTION, PHASE1_PROFILE_DISTRIBUTION
)

# Alias for backward compatibility
PROFILE_DISTRIBUTION = BALANCED_PROFILE_DISTRIBUTION


class VendorGenerator:
    """Generates synthetic vendor population with reproducible profiles."""

    def __init__(self, seed: int = 42, profile_distribution: Optional[List[Tuple[str, float]]] = None):
        self.rng = random.Random(seed)
        self.profile_distribution = profile_distribution or BALANCED_PROFILE_DISTRIBUTION

    def generate_vendors(self, count: int = 100) -> List[Vendor]:
        vendors: List[Vendor] = []
        states, state_names, state_weights = zip(*[(s[0], s[1], s[2]) for s in INDIAN_STATES_DATA])
        profile_codes, profile_weights = zip(*self.profile_distribution)

        for i in range(1, count + 1):
            vid = f"V{i:04d}"
            
            # Weighted state selection
            chosen_state_idx = self.rng.choices(range(len(states)), weights=state_weights, k=1)[0]
            st_code = states[chosen_state_idx]
            st_name = state_names[chosen_state_idx]
            
            # Weighted profile selection
            profile_code = self.rng.choices(profile_codes, weights=profile_weights, k=1)[0]
            
            # Company name
            prefix = self.rng.choice(COMPANY_PREFIXES)
            suffix = self.rng.choice(COMPANY_SUFFIXES)
            name = f"{prefix} {suffix} ({vid})"

            gstin = make_gstin(st_code, i)
            category = self.rng.choice(BUSINESS_CATEGORIES)
            
            # Registration date between 2017 and 2023
            reg_year = self.rng.randint(2017, 2023)
            reg_month = self.rng.randint(1, 12)
            reg_day = self.rng.randint(1, 28)

            vendor = Vendor(
                vendor_id=vid,
                vendor_name=name,
                gstin=gstin,
                state=st_name,
                state_code=st_code,
                business_category=category,
                registration_date=date(reg_year, reg_month, reg_day),
                is_active=True,
                synthetic_profile=profile_code
            )
            vendors.append(vendor)

        return vendors
