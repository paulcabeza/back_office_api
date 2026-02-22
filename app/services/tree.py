"""
Binary tree service: builds the genealogy tree structure for visualization.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliate import Affiliate
from app.schemas.affiliate import TreeNodeResponse


async def get_binary_tree(
    db: AsyncSession,
    root_id: uuid.UUID,
    depth: int = 3,
) -> TreeNodeResponse | None:
    """Build the binary tree starting from root_id, up to `depth` levels.

    Returns a TreeNodeResponse with nested left_child/right_child,
    or None if the root affiliate is not found.
    """
    result = await db.execute(
        select(Affiliate).where(
            Affiliate.id == root_id,
            Affiliate.deleted_at.is_(None),
        )
    )
    root = result.scalar_one_or_none()
    if root is None:
        return None

    return await _build_node(db, root, depth)


async def _build_node(
    db: AsyncSession,
    affiliate: Affiliate,
    remaining_depth: int,
) -> TreeNodeResponse:
    """Recursively build a tree node with its children."""
    left_child = None
    right_child = None

    if remaining_depth > 0:
        # Query both children in a single query
        result = await db.execute(
            select(Affiliate).where(
                Affiliate.placement_parent_id == affiliate.id,
                Affiliate.deleted_at.is_(None),
            )
        )
        children = result.scalars().all()

        for child in children:
            if child.placement_side == "left":
                left_child = await _build_node(db, child, remaining_depth - 1)
            elif child.placement_side == "right":
                right_child = await _build_node(db, child, remaining_depth - 1)

    return TreeNodeResponse(
        id=affiliate.id,
        affiliate_code=affiliate.affiliate_code,
        full_name=affiliate.full_name,
        status=affiliate.status,
        current_rank=affiliate.current_rank,
        pv_current_period=affiliate.pv_current_period,
        bv_left_total=affiliate.bv_left_total,
        bv_right_total=affiliate.bv_right_total,
        enrolled_at=affiliate.enrolled_at,
        left_child=left_child,
        right_child=right_child,
    )
