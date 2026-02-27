"""Pure Pydantic validation tests — no mocks, no DB."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.affiliate import EnrollmentRequest

# ── Helpers ──────────────────────────────────────────────────────────────

BASE_DATA = {
    "first_name": "Roberto",
    "last_name": "Cabrera Lopez",
    "email": "rob@example.com",
    "kit_tier": "ESP1",
    "password": "secure1234",
    "tax_id_type": "NIT",
    "tax_id_number": "0614-010190-101-0",
}


def enrollment(**overrides):
    return EnrollmentRequest(**{**BASE_DATA, **overrides})


# ── Tests ────────────────────────────────────────────────────────────────

def test_valid_enrollment_without_sponsor():
    """First distributor in the network — no sponsor, no placement."""
    aff = enrollment()
    assert aff.first_name == "Roberto"
    assert aff.sponsor_id is None


def test_sponsor_requires_placement_parent():
    """If sponsor_id is given, placement_parent_id must also be given."""
    with pytest.raises(ValidationError, match="placement_parent_id is required"):
        enrollment(sponsor_id=uuid.uuid4())


def test_sponsor_requires_placement_side():
    """If sponsor_id is given, placement_side must also be given."""
    with pytest.raises(ValidationError, match="placement_side is required"):
        enrollment(sponsor_id=uuid.uuid4(), placement_parent_id=uuid.uuid4())


def test_no_documents_fails():
    """At least one document (ID or tax) is required."""
    data = {**BASE_DATA}
    data.pop("tax_id_type")
    data.pop("tax_id_number")
    with pytest.raises(ValidationError, match="At least one document"):
        EnrollmentRequest(**data)


def test_only_tax_id_is_valid():
    """Having only tax ID (no identity doc) should be valid."""
    aff = enrollment(id_doc_type=None, id_doc_number=None)
    assert aff.tax_id_number == "0614-010190-101-0"
