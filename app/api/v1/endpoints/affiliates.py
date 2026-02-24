import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status as http_status

from app.core.deps import get_current_user, require_permission
from app.db.session import get_db
from app.models.affiliate import Affiliate
from app.models.user import User
from app.schemas.affiliate import AffiliateListResponse, AffiliateResponse, EnrollmentRequest, TreeNodeResponse
from app.schemas.order import EnrollmentResponse, OrderResponse
from app.services.email import send_enrollment_notification_admin, send_welcome_distributor
from app.services.enrollment import enroll_affiliate
from app.services.tree import get_binary_tree

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/affiliates", tags=["affiliates"])


@router.post("/enroll", response_model=EnrollmentResponse, status_code=201)
async def enroll(
    body: EnrollmentRequest,
    current_user: User = Depends(require_permission("affiliates:create")),
    db: AsyncSession = Depends(get_db),
):
    """Enroll a new affiliate: creates the affiliate + enrollment order (kit purchase)."""
    affiliate, order = await enroll_affiliate(db, body, current_user.id)

    # Send notification emails (non-blocking, failures are logged but don't affect response)
    kit_item = order.items[0] if order.items else None
    kit_name = kit_item.product.name if kit_item else body.kit_tier
    kit_price = str(order.total)

    placement_info = None
    if affiliate.placement_parent_id and affiliate.placement_side:
        placement_info = f"Pierna {affiliate.placement_side}"

    sponsor_name = None
    if affiliate.sponsor_id:
        result = await db.execute(
            select(Affiliate.first_name, Affiliate.last_name).where(
                Affiliate.id == affiliate.sponsor_id
            )
        )
        sponsor_row = result.one_or_none()
        if sponsor_row:
            sponsor_name = f"{sponsor_row.first_name} {sponsor_row.last_name}"

    try:
        send_welcome_distributor(
            to_email=affiliate.email,
            first_name=affiliate.first_name,
            last_name=affiliate.last_name,
            affiliate_code=affiliate.affiliate_code,
            kit_name=kit_name,
            kit_price=kit_price,
            sponsor_name=sponsor_name,
        )
        send_enrollment_notification_admin(
            admin_email=current_user.email,
            admin_name=current_user.full_name,
            affiliate_code=affiliate.affiliate_code,
            affiliate_name=f"{affiliate.first_name} {affiliate.last_name}",
            affiliate_email=affiliate.email,
            kit_name=kit_name,
            kit_price=kit_price,
            order_number=order.order_number,
            placement_info=placement_info,
        )
    except Exception:
        logger.exception("Failed to send enrollment emails for %s", affiliate.affiliate_code)

    return EnrollmentResponse(
        affiliate=AffiliateResponse.model_validate(affiliate),
        order=OrderResponse.model_validate(order),
    )


@router.get("/me", response_model=AffiliateResponse)
async def get_my_affiliate(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the affiliate profile linked to the current user."""
    result = await db.execute(
        select(Affiliate).where(
            Affiliate.user_id == current_user.id,
            Affiliate.deleted_at.is_(None),
        )
    )
    affiliate = result.scalar_one_or_none()
    if affiliate is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="No affiliate profile linked to this user",
        )
    return AffiliateResponse.model_validate(affiliate)


@router.get("", response_model=list[AffiliateListResponse])
async def list_affiliates(
    current_user: User = Depends(require_permission("affiliates:read")),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(default=None, description="Filter by status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List affiliates with optional status filter and pagination."""
    query = select(Affiliate).where(Affiliate.deleted_at.is_(None))
    if status:
        query = query.where(Affiliate.status == status)
    query = query.order_by(Affiliate.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    affiliates = result.scalars().all()
    return [AffiliateListResponse.model_validate(a) for a in affiliates]


@router.get("/{affiliate_id}", response_model=AffiliateResponse)
async def get_affiliate(
    affiliate_id: uuid.UUID,
    current_user: User = Depends(require_permission("affiliates:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single affiliate by ID."""
    result = await db.execute(
        select(Affiliate).where(
            Affiliate.id == affiliate_id,
            Affiliate.deleted_at.is_(None),
        )
    )
    affiliate = result.scalar_one_or_none()
    if affiliate is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Affiliate not found")
    return AffiliateResponse.model_validate(affiliate)


@router.get("/{affiliate_id}/tree", response_model=TreeNodeResponse)
async def get_affiliate_tree(
    affiliate_id: uuid.UUID,
    current_user: User = Depends(require_permission("affiliates:read")),
    db: AsyncSession = Depends(get_db),
    depth: int = Query(default=3, ge=1, le=10, description="Tree depth levels"),
):
    """Get the binary tree starting from an affiliate, up to `depth` levels."""
    tree = await get_binary_tree(db, affiliate_id, depth)
    if tree is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Affiliate not found",
        )
    return tree
