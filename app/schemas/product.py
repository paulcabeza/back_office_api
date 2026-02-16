import uuid
from decimal import Decimal

from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    description: str | None
    category: str
    price_public: Decimal
    price_distributor: Decimal
    currency: str
    pv: Decimal
    bv: Decimal
    is_kit: bool
    kit_tier: str | None
    status: str

    model_config = {"from_attributes": True}
