import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class Affiliate(BaseModel):
    __tablename__ = "affiliates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "affiliate_code", name="uq_affiliates_tenant_code"),
        UniqueConstraint("tenant_id", "email", name="uq_affiliates_tenant_email"),
        CheckConstraint("placement_side IN ('left', 'right')", name="chk_placement_side"),
        CheckConstraint("status IN ('pending', 'active', 'inactive', 'suspended', 'cancelled')", name="chk_affiliate_status"),
        CheckConstraint("kit_tier IN ('ESP1', 'ESP2', 'ESP3')", name="chk_kit_tier"),
        CheckConstraint("sponsor_id IS DISTINCT FROM id", name="chk_no_self_sponsor"),
        CheckConstraint("placement_parent_id IS DISTINCT FROM id", name="chk_no_self_placement"),
    )

    # Link to admin user (optional 1:1)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=True
    )
    # Who (admin/staff) created this affiliate record
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    affiliate_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True
    )
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, default="SV")

    # Personal data
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Identity document (DUI, Cedula, INE, Passport)
    id_doc_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    id_doc_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Tax ID (NIT, RFC, RUC, RUT)
    tax_id_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tax_id_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Address
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state_province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # MLM network
    sponsor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("affiliates.id"), nullable=True, index=True
    )
    placement_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("affiliates.id"), nullable=True
    )
    placement_side: Mapped[str | None] = mapped_column(String(5), nullable=True)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    kit_tier: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Status and rank
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    current_rank: Mapped[str] = mapped_column(String(30), nullable=False, default="affiliate")
    highest_rank: Mapped[str] = mapped_column(String(30), nullable=False, default="affiliate")

    # Volume accumulators (denormalized, updated on order payment)
    pv_current_period: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    bv_left_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    bv_right_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    bv_left_carry: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    bv_right_carry: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    sponsor: Mapped["Affiliate | None"] = relationship(
        "Affiliate", remote_side="Affiliate.id", foreign_keys=[sponsor_id]
    )
    placement_parent: Mapped["Affiliate | None"] = relationship(
        "Affiliate", remote_side="Affiliate.id", foreign_keys=[placement_parent_id]
    )
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="affiliate")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
