import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel
from app.models.associations import user_roles


class Role(BaseModel):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships — explicit join because user_roles has 2 FKs to users
    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions", back_populates="roles", lazy="selectin"
    )
    users: Mapped[list["User"]] = relationship(
        secondary=user_roles,
        primaryjoin="Role.id == user_roles.c.role_id",
        secondaryjoin="User.id == user_roles.c.user_id",
        back_populates="roles",
        lazy="selectin",
    )


class Permission(BaseModel):
    __tablename__ = "permissions"

    codename: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        secondary="role_permissions", back_populates="permissions", lazy="selectin"
    )
