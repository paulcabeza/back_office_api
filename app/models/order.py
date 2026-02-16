import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class Order(BaseModel):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "order_type IN ('enrollment', 'repurchase', 'autoship', 'admin')",
            name="chk_order_type",
        ),
        CheckConstraint(
            "status IN ('pending_payment', 'paid', 'in_preparation', 'shipped', 'delivered', 'cancelled', 'returned')",
            name="chk_order_status",
        ),
    )

    order_number: Mapped[str] = mapped_column(
        String(30), nullable=False, unique=True
    )
    affiliate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("affiliates.id"), nullable=False, index=True
    )
    order_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="enrollment"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending_payment", index=True
    )

    # Totals
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Volume totals
    total_pv: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total_bv: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Payment
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Shipping
    shipping_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    affiliate: Mapped["Affiliate"] = relationship("Affiliate", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(BaseModel):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Snapshot at time of purchase (prices/volumes may change later)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    pv: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    bv: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_pv: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    line_bv: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", lazy="selectin")
