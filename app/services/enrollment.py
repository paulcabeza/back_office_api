"""
Enrollment service: creates a new affiliate + enrollment order in a single transaction.
This is the core business flow for Phase 1 MVP.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.affiliate import Affiliate
from app.models.associations import user_roles
from app.models.audit_log import AuditLog
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.role import Role
from app.models.user import User
from app.schemas.affiliate import EnrollmentRequest


async def generate_affiliate_code(db: AsyncSession, country_code: str) -> str:
    """Generate next affiliate code using PostgreSQL sequence.

    Format: GH-{COUNTRY}-{SEQ:06d} (e.g. GH-SV-000001)
    Creates the sequence if it doesn't exist yet.
    """
    seq_name = f"affiliate_seq_{country_code.lower()}"

    # Create sequence if not exists (idempotent)
    await db.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq_name} START 1 INCREMENT 1"))

    result = await db.execute(text(f"SELECT nextval('{seq_name}')"))
    seq_val = result.scalar()

    return f"GH-{country_code.upper()}-{seq_val:06d}"


async def generate_order_number(db: AsyncSession) -> str:
    """Generate next order number: ORD-YYYYMMDD-XXXX."""
    await db.execute(text("CREATE SEQUENCE IF NOT EXISTS order_seq START 1 INCREMENT 1"))

    result = await db.execute(text("SELECT nextval('order_seq')"))
    seq_val = result.scalar()

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"ORD-{date_str}-{seq_val:04d}"


async def enroll_affiliate(
    db: AsyncSession,
    request: EnrollmentRequest,
    created_by_user_id: uuid.UUID,
) -> tuple[Affiliate, Order]:
    """Create a new affiliate and their enrollment order atomically.

    Returns (affiliate, order) tuple.
    Raises HTTPException on validation errors.
    """

    # 1. Validate sponsor exists (if provided)
    if request.sponsor_id:
        result = await db.execute(
            select(Affiliate).where(
                Affiliate.id == request.sponsor_id,
                Affiliate.deleted_at.is_(None),
            )
        )
        sponsor = result.scalar_one_or_none()
        if sponsor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sponsor not found",
            )
    else:
        # Sponsor is required if there are already affiliates in the system
        result = await db.execute(
            select(Affiliate.id).where(Affiliate.deleted_at.is_(None)).limit(1)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Sponsor is required",
            )

    # 2. Validate placement position is available (if provided)
    if request.placement_parent_id:
        # Check parent exists
        result = await db.execute(
            select(Affiliate).where(
                Affiliate.id == request.placement_parent_id,
                Affiliate.deleted_at.is_(None),
            )
        )
        parent = result.scalar_one_or_none()
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Placement parent not found",
            )

        # Check position is not taken
        result = await db.execute(
            select(Affiliate).where(
                Affiliate.placement_parent_id == request.placement_parent_id,
                Affiliate.placement_side == request.placement_side,
                Affiliate.deleted_at.is_(None),
            )
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Position '{request.placement_side}' under this parent is already taken",
            )

    # 3. Check email uniqueness (in both users and affiliates tables)
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    result = await db.execute(
        select(Affiliate).where(
            Affiliate.email == request.email,
            Affiliate.deleted_at.is_(None),
        )
    )
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An affiliate with this email already exists",
        )

    # 4. Find the kit product
    result = await db.execute(
        select(Product).where(
            Product.is_kit.is_(True),
            Product.kit_tier == request.kit_tier,
            Product.status == "active",
        )
    )
    kit = result.scalar_one_or_none()
    if kit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kit {request.kit_tier} not found or inactive",
        )

    # 5. Generate codes
    affiliate_code = await generate_affiliate_code(db, request.country_code)
    order_number = await generate_order_number(db)

    # 6. Create user account for the distributor
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        is_active=True,
        is_superadmin=False,
    )
    db.add(user)
    await db.flush()  # get user.id

    # Assign distributor role
    result = await db.execute(
        select(Role).where(Role.name == "distributor")
    )
    distributor_role = result.scalar_one_or_none()
    if distributor_role:
        await db.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=distributor_role.id,
                assigned_by=created_by_user_id,
            )
        )

    # 7. Create affiliate linked to user
    affiliate = Affiliate(
        user_id=user.id,
        created_by_user_id=created_by_user_id,
        affiliate_code=affiliate_code,
        country_code=request.country_code.upper(),
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        phone=request.phone,
        date_of_birth=request.date_of_birth,
        id_doc_type=request.id_doc_type,
        id_doc_number=request.id_doc_number,
        tax_id_type=request.tax_id_type,
        tax_id_number=request.tax_id_number,
        address_line1=request.address_line1,
        address_line2=request.address_line2,
        city=request.city,
        state_province=request.state_province,
        postal_code=request.postal_code,
        sponsor_id=request.sponsor_id,
        placement_parent_id=request.placement_parent_id,
        placement_side=request.placement_side,
        kit_tier=request.kit_tier,
        status="pending",
    )
    db.add(affiliate)
    await db.flush()  # get affiliate.id

    # 8. Create enrollment order
    order_item = OrderItem(
        product_id=kit.id,
        quantity=1,
        unit_price=kit.price_distributor,
        pv=kit.pv,
        bv=kit.bv,
        line_total=kit.price_distributor,
        line_pv=kit.pv,
        line_bv=kit.bv,
    )

    order = Order(
        order_number=order_number,
        affiliate_id=affiliate.id,
        order_type="enrollment",
        status="pending_payment",
        subtotal=kit.price_distributor,
        total=kit.price_distributor,
        total_pv=kit.pv,
        total_bv=kit.bv,
        created_by=created_by_user_id,
        items=[order_item],
    )
    db.add(order)

    # 9. Audit log
    audit = AuditLog(
        tenant_id=affiliate.tenant_id,
        user_id=created_by_user_id,
        action="affiliate.enroll",
        resource_type="affiliate",
        resource_id=affiliate.id,
        new_values={
            "affiliate_code": affiliate_code,
            "email": request.email,
            "kit_tier": request.kit_tier,
            "sponsor_id": str(request.sponsor_id) if request.sponsor_id else None,
            "order_number": order_number,
        },
    )
    db.add(audit)

    await db.flush()

    # Refresh to eager-load relationships (items -> product) for serialization
    await db.refresh(order, ["items"])
    for item in order.items:
        await db.refresh(item, ["product"])

    return affiliate, order
