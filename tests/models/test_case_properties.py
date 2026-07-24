"""Property-based tests for CaseModel.

Strategies and helpers are defined here and imported by the individual
property test functions added in subsequent tasks (5.2 – 5.9).
"""

import uuid

from hypothesis import given, settings, assume
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

# Strategy for valid severity values
valid_severity = st.sampled_from(["low", "medium", "high", "critical"])

# Strategy for valid emails (non-empty local@domain, max 254 chars)
valid_email = st.from_regex(
    r"[a-z0-9]{1,64}@[a-z]{1,63}\.[a-z]{2,10}", fullmatch=True
).filter(lambda e: len(e) <= 254)

# Strategy for valid UUIDs
valid_uuid = st.uuids()

# Strategy for a complete valid CaseModel dict
valid_case_dict = st.fixed_dictionaries(
    {
        "case_id": valid_uuid,
        "email": valid_email,
        "issue": st.text(min_size=1, max_size=2000),
        "response": st.text(max_size=5000),
        "severity": valid_severity,
    }
)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _is_valid_uuid(s: str) -> bool:
    """Return True if *s* is a valid RFC 4122 UUID string representation."""
    try:
        uuid.UUID(str(s))
        return True
    except (ValueError, AttributeError):
        return False
