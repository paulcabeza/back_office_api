import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_permission
from app.db.session import get_db
from app.models.order import Order
from app.models.user import User
from app.schemas.order import ConfirmPaymentRequest, OrderResponse
from app.services.payment import confirm_payment

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(require_permission("orders:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single order by ID with its items."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return OrderResponse.model_validate(order)


@router.patch("/{order_id}/confirm-payment", response_model=OrderResponse)
async def confirm_order_payment(
    order_id: uuid.UUID,
    body: ConfirmPaymentRequest,
    current_user: User = Depends(require_permission("orders:update")),
    db: AsyncSession = Depends(get_db),
):
    """Confirm payment for an order. Accrues BV/PV and activates affiliate if enrollment."""
    order = await confirm_payment(
        db=db,
        order_id=order_id,
        payment_method=body.payment_method,
        payment_reference=body.payment_reference,
        confirmed_by_user_id=current_user.id,
    )
    return OrderResponse.model_validate(order)
