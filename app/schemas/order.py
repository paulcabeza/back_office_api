import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.affiliate import AffiliateResponse
from app.schemas.product import ProductResponse


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product: ProductResponse
    quantity: int
    unit_price: Decimal
    pv: Decimal
    bv: Decimal
    line_total: Decimal
    line_pv: Decimal
    line_bv: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    affiliate_id: uuid.UUID
    order_type: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    total_pv: Decimal
    total_bv: Decimal
    payment_method: str | None
    paid_at: datetime | None
    items: list[OrderItemResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class EnrollmentResponse(BaseModel):
    """Response for the enrollment endpoint: new affiliate + their enrollment order."""
    affiliate: AffiliateResponse
    order: OrderResponse
