import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.security import hash_password
from app.db.session import get_db
from app.models.associations import user_roles
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    RoleResponse,
    UpdateUserRequest,
    UserCreate,
    UserListResponse,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    current_user: User = Depends(require_permission("users:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new admin/staff user with assigned roles."""
    # Check email uniqueness
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # Validate roles exist
    roles: list[Role] = []
    for role_id in body.role_ids:
        result = await db.execute(select(Role).where(Role.id == role_id))
        role = result.scalar_one_or_none()
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} not found",
            )
        if role.name == "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign super_admin role via this endpoint",
            )
        roles.append(role)

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        is_active=True,
        is_superadmin=False,
    )
    db.add(user)
    await db.flush()

    # Assign roles
    for role in roles:
        await db.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=role.id,
                assigned_by=current_user.id,
            )
        )

    await db.commit()
    await db.refresh(user, ["roles"])

    return UserResponse.model_validate(user)


@router.get("", response_model=list[UserListResponse])
async def list_users(
    current_user: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List all users with pagination."""
    query = (
        select(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    users = result.scalars().all()
    return [UserListResponse.model_validate(u) for u in users]


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    current_user: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db),
):
    """List all available roles (for dropdowns)."""
    result = await db.execute(select(Role).order_by(Role.display_name))
    roles = result.scalars().all()
    return [RoleResponse.model_validate(r) for r in roles]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission("users:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UpdateUserRequest,
    current_user: User = Depends(require_permission("users:update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's profile, status, or role."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_superadmin and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify a superadmin user",
        )

    # Prevent user from deactivating themselves
    if body.is_active is False and user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta",
        )

    # Update scalar fields
    if body.email is not None:
        # Check uniqueness
        result = await db.execute(
            select(User).where(User.email == body.email, User.id != user_id)
        )
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )
        user.email = body.email

    if body.first_name is not None:
        user.first_name = body.first_name
    if body.last_name is not None:
        user.last_name = body.last_name
    if body.is_active is not None:
        user.is_active = body.is_active

    # Update role (replace all non-super_admin roles with the new one)
    if body.role_id is not None:
        result = await db.execute(select(Role).where(Role.id == body.role_id))
        new_role = result.scalar_one_or_none()
        if new_role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {body.role_id} not found",
            )
        if new_role.name == "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign super_admin role via this endpoint",
            )

        # Remove existing roles and assign the new one
        await db.execute(
            user_roles.delete().where(user_roles.c.user_id == user.id)
        )
        await db.execute(
            user_roles.insert().values(
                user_id=user.id,
                role_id=new_role.id,
                assigned_by=current_user.id,
            )
        )

    await db.commit()
    await db.refresh(user, ["roles"])

    return UserResponse.model_validate(user)
