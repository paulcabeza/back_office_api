from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BaseModel


class Product(BaseModel):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),
        CheckConstraint("status IN ('active', 'inactive', 'discontinued')", name="chk_product_status"),
        CheckConstraint("kit_tier IN ('ESP1', 'ESP2', 'ESP3')", name="chk_product_kit_tier"),
    )

    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")

    # Pricing
    price_public: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_distributor: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Volumes
    pv: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    bv: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=0)

    # Kit fields
    is_kit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    kit_tier: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    country_availability: Mapped[list[str]] = mapped_column(
        ARRAY(String(2)), nullable=False, server_default="{SV}"
    )

    # Basic stock tracking (full inventory module in later phase)
    track_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
