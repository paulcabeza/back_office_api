import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "assigned_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    ),
    Column(
        "assigned_by",
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    ),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
