import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.db.session import get_db
from app.models.affiliate import Affiliate
from app.models.user import User
from app.schemas.affiliate import AffiliateListResponse, AffiliateResponse, EnrollmentRequest
from app.schemas.order import EnrollmentResponse, OrderResponse
from app.services.enrollment import enroll_affiliate

router = APIRouter(prefix="/affiliates", tags=["affiliates"])


@router.post("/enroll", response_model=EnrollmentResponse, status_code=201)
async def enroll(
    body: EnrollmentRequest,
    current_user: User = Depends(require_permission("affiliates:create")),
    db: AsyncSession = Depends(get_db),
):
    """Enroll a new affiliate: creates the affiliate + enrollment order (kit purchase)."""
    affiliate, order = await enroll_affiliate(db, body, current_user.id)
    return EnrollmentResponse(
        affiliate=AffiliateResponse.model_validate(affiliate),
        order=OrderResponse.model_validate(order),
    )


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
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Affiliate not found")
    return AffiliateResponse.model_validate(affiliate)
