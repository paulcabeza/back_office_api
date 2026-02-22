import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


class EnrollmentRequest(BaseModel):
    """Create a new affiliate with enrollment order (kit purchase) in one step."""

    # Personal data
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    date_of_birth: date | None = None
    country_code: str = Field(default="SV", min_length=2, max_length=2)

    # Documents — at least one pair required (app-level validation)
    id_doc_type: str | None = Field(default=None, max_length=20)
    id_doc_number: str | None = Field(default=None, max_length=50)
    tax_id_type: str | None = Field(default=None, max_length=20)
    tax_id_number: str | None = Field(default=None, max_length=50)

    # Address
    address_line1: str | None = Field(default=None, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state_province: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)

    # MLM placement
    sponsor_id: uuid.UUID | None = None
    placement_parent_id: uuid.UUID | None = None
    placement_side: Literal["left", "right"] | None = None

    # Kit selection
    kit_tier: Literal["ESP1", "ESP2", "ESP3"]

    # Distributor login credentials
    password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_documents(self):
        has_id = self.id_doc_type and self.id_doc_number
        has_tax = self.tax_id_type and self.tax_id_number
        if not has_id and not has_tax:
            raise ValueError("At least one document is required (identity or tax ID)")
        return self

    @model_validator(mode="after")
    def validate_placement(self):
        if self.placement_parent_id and not self.placement_side:
            raise ValueError("placement_side is required when placement_parent_id is provided")
        return self


class AffiliateResponse(BaseModel):
    id: uuid.UUID
    affiliate_code: str
    country_code: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: str | None
    status: str
    kit_tier: str | None
    current_rank: str
    highest_rank: str
    sponsor_id: uuid.UUID | None
    placement_parent_id: uuid.UUID | None
    placement_side: str | None
    pv_current_period: Decimal
    bv_left_total: Decimal
    bv_right_total: Decimal
    enrolled_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AffiliateListResponse(BaseModel):
    id: uuid.UUID
    affiliate_code: str
    full_name: str
    email: str
    status: str
    kit_tier: str | None
    current_rank: str
    enrolled_at: datetime

    model_config = {"from_attributes": True}
