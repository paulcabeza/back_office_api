"""
Payment confirmation service: marks an order as paid and accrues BV/PV.

This is the ONLY place where volume (BV/PV) gets credited to the network.
Business Rule #4: BV only from paid orders.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate import Affiliate
from app.models.audit_log import AuditLog
from app.models.order import Order


async def confirm_payment(
    db: AsyncSession,
    order_id: uuid.UUID,
    payment_method: str,
    payment_reference: str | None,
    confirmed_by_user_id: uuid.UUID,
) -> Order:
    """Confirm payment for an order: update status, accrue PV/BV, activate affiliate.

    In a single transaction:
    1. Validate order is in pending_payment status.
    2. Mark order as paid.
    3. Accrue PV to the affiliate (pv_current_period).
    4. Accrue BV upward through the binary tree to all ancestors.
    5. If enrollment order: activate the affiliate (pending -> active).
    6. Audit log.

    Returns the updated order.
    """

    # 1. Load order
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    if order.status != "pending_payment":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Order is already '{order.status}', cannot confirm payment",
        )

    # 2. Mark order as paid
    old_status = order.status
    order.status = "paid"
    order.payment_method = payment_method
    order.payment_reference = payment_reference
    order.paid_at = datetime.now(timezone.utc)

    # 3. Load the affiliate and accrue PV
    result = await db.execute(
        select(Affiliate).where(Affiliate.id == order.affiliate_id)
    )
    affiliate = result.scalar_one()

    affiliate.pv_current_period += order.total_pv

    # 4. Accrue BV upward through the binary tree
    await _accrue_bv_to_upline(db, affiliate, order.total_bv)

    # 5. Activate affiliate if this is an enrollment order
    if order.order_type == "enrollment" and affiliate.status == "pending":
        affiliate.status = "active"

    # 6. Audit log
    audit = AuditLog(
        tenant_id=affiliate.tenant_id,
        user_id=confirmed_by_user_id,
        action="order.confirm_payment",
        resource_type="order",
        resource_id=order.id,
        old_values={"status": old_status},
        new_values={
            "status": "paid",
            "payment_method": payment_method,
            "payment_reference": payment_reference,
            "pv_accrued": str(order.total_pv),
            "bv_accrued": str(order.total_bv),
            "affiliate_activated": order.order_type == "enrollment" and old_status == "pending",
        },
    )
    db.add(audit)

    await db.flush()

    # Refresh order with items for response serialization
    await db.refresh(order, ["items"])
    for item in order.items:
        await db.refresh(item, ["product"])

    return order


async def _accrue_bv_to_upline(
    db: AsyncSession,
    affiliate: Affiliate,
    bv_amount: Decimal,
) -> None:
    """Walk up the binary tree from the affiliate, adding BV to the correct leg of each ancestor.

    For each ancestor:
    - If the affiliate falls on the LEFT side -> ancestor.bv_left_total += bv_amount
    - If the affiliate falls on the RIGHT side -> ancestor.bv_right_total += bv_amount

    Example:
        Tree:       A
                   / \\
                  B   C
                 /
                D  <- affiliate (bought kit, BV=300)

        D is left child of B -> B.bv_left_total += 300
        B is left child of A -> A.bv_left_total += 300
    """
    current = affiliate

    while current.placement_parent_id is not None:
        side = current.placement_side  # "left" or "right"

        # Load parent
        result = await db.execute(
            select(Affiliate).where(Affiliate.id == current.placement_parent_id)
        )
        parent = result.scalar_one_or_none()
        if parent is None:
            break  # safety: broken tree link

        # Accrue to the correct leg
        if side == "left":
            parent.bv_left_total += bv_amount
        elif side == "right":
            parent.bv_right_total += bv_amount

        # Move up
        current = parent
