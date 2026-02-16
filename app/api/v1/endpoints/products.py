from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.db.session import get_db
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductResponse])
async def list_products(
    current_user: User = Depends(require_permission("products:read")),
    db: AsyncSession = Depends(get_db),
    kits_only: bool = Query(default=False, description="Filter to only show enrollment kits"),
):
    """List active products. Use kits_only=true to see only enrollment kits."""
    query = select(Product).where(Product.status == "active")
    if kits_only:
        query = query.where(Product.is_kit.is_(True))
    query = query.order_by(Product.name)

    result = await db.execute(query)
    return [ProductResponse.model_validate(p) for p in result.scalars().all()]
