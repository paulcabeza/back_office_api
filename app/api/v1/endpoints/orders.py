import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import require_permission
from app.db.session import get_db
from app.models.affiliate import Affiliate
from app.models.order import Order
from app.models.user import User
from app.schemas.order import ConfirmPaymentRequest, OrderListResponse, OrderResponse
from app.services.payment import confirm_payment

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[OrderListResponse])
async def list_orders(
    current_user: User = Depends(require_permission("orders:read")),
    db: AsyncSession = Depends(get_db),
    order_status: str | None = Query(default="pending_payment", alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List orders with optional status filter. Defaults to pending_payment."""
    query = select(Order)
    if order_status:
        query = query.where(Order.status == order_status)
    query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    orders = result.scalars().all()

    # Batch-resolve affiliate names
    affiliate_ids = {o.affiliate_id for o in orders}
    affiliate_map: dict[uuid.UUID, tuple[str, str]] = {}
    if affiliate_ids:
        aff_result = await db.execute(
            select(Affiliate.id, Affiliate.first_name, Affiliate.last_name, Affiliate.affiliate_code).where(
                Affiliate.id.in_(affiliate_ids)
            )
        )
        for row in aff_result:
            affiliate_map[row.id] = (f"{row.first_name} {row.last_name}", row.affiliate_code)

    responses = []
    for o in orders:
        resp = OrderListResponse.model_validate(o)
        name, code = affiliate_map.get(o.affiliate_id, ("", ""))
        resp.affiliate_name = name
        resp.affiliate_code = code
        responses.append(resp)
    return responses


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
